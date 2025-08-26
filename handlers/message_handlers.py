import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
from handlers.callbacks import *
from locales.ru import get_text
from utils import escape_markdown_v2, get_user_identification, get_course_flow_info
from utils.courses import get_course_by_id
from utils.lessons import get_lesson_by_type
from db import bookings as db_bookings
from db import events as db_events
from db import free_lessons as db_free_lessons

logger = logging.getLogger(__name__)


def _build_admin_notification_caption(user, booking_record, message_type, status_text=None):
    """
    Строит caption для уведомления админа
    
    Args:
        user: Telegram User объект
        booking_record: Запись о бронировании из БД
        message_type: Тип сообщения ('photo_check', 'student_response', 'alternative_payment')
        status_text: Текст статуса (необязательный)
    
    Returns:
        str: Готовый caption для админа
    """
    from utils import get_user_identification, get_course_flow_info, escape_markdown_v2
    from utils.courses import get_course_by_id
    
    booking_id = booking_record['id']
    course_name = booking_record.get('course_name', "Неизвестный курс")
    course_stream = booking_record.get('course_stream', '4th_stream')
    course_id = booking_record.get('course_id')
    
    # Get start date and format course flow info
    course = get_course_by_id(course_id) if course_id else None
    start_date_text = course.get('start_date_text', 'дата не указана') if course else 'дата не указана'
    course_flow_info = get_course_flow_info(course_stream, start_date_text)
    
    # Enhanced user identification
    user_identification = get_user_identification({
        'username': user.username,
        'first_name': user.first_name,
        'user_id': user.id
    })
    
    # Message-specific header
    if message_type == 'photo_check':
        header = r"🧾 *Новый чек для проверки\\!*"
    elif message_type == 'student_response':
        header = "💬 *Ответ студента*"
    elif message_type == 'alternative_payment':
        header = r"📩 *Альтернативное подтверждение оплаты\\!*"
    else:
        header = "📨 *Сообщение от студента*"
    
    caption = (
        f"{header}\\n"
        rf"Пользователь: {escape_markdown_v2(user_identification)} \\(ID: `{user.id}`\\)\\n"
        f"Заявка №: *{escape_markdown_v2(str(booking_id))}*\\n"
        f"Курс: *{escape_markdown_v2(course_name)}*\\n"
        f"Поток: *{escape_markdown_v2(course_flow_info)}*"
    )
    
    if status_text:
        caption += f"\\nСтатус: {escape_markdown_v2(status_text)}"
    
    return caption


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles photo uploads for payment confirmation."""
    user = update.message.from_user
    db_events.log_event(
        user.id, 
        'payment_proof_uploaded',
        username=user.username,
        first_name=user.first_name
    )
    logger.info(f"Photo received from user {user.id} ({user.first_name})")

    booking_record = db_bookings.get_pending_booking_by_user(user.id)

    if not booking_record:
        logger.warning(f"Photo from user {user.id} received, but no active booking found.")
        await update.message.reply_text("Не могу найти активную заявку для вас. Пожалуйста, сначала выберите курс.")
        return

    booking_id = booking_record['id']
    course_name = booking_record['course_name']
    course_stream = booking_record.get('course_stream', '4th_stream')
    
    if not db_bookings.update_booking_status(booking_id, 1):
        await update.message.reply_text("Произошла ошибка при обновлении статуса заявки.")
        return

    logger.info(f"Booking {booking_id} for user {user.id} updated to 'payment uploaded' status (1).")

    await update.message.reply_text(
        rf"🙏 Спасибо, {escape_markdown_v2(user.first_name)}\! Ваше фото для заявки №*{escape_markdown_v2(str(booking_id))}* "
        rf"\(курс '*{escape_markdown_v2(course_name)}*' \) получено\.\n"
        r"Оплата проверяется\. Мы сообщим вам о результате\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    if config.TARGET_CHAT_ID == 0:
        logger.error("TARGET_CHAT_ID is not set. Cannot forward photo to admin.")
        return

    caption_for_admin = _build_admin_notification_caption(user, booking_record, 'photo_check')

    forwarded_message = await context.bot.forward_message(
        chat_id=config.TARGET_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )

    admin_keyboard = [[
        InlineKeyboardButton(
            f"✅ Одобрить ({booking_id})",
            callback_data=f"{CALLBACK_ADMIN_APPROVE_PAYMENT}{user.id}_{booking_id}"
        )
    ]]
    await context.bot.send_message(
        chat_id=config.TARGET_CHAT_ID,
        text=caption_for_admin,
        reply_markup=InlineKeyboardMarkup(admin_keyboard),
        reply_to_message_id=forwarded_message.message_id,
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def any_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles any message (text, video, document, etc.) when user has active booking or awaiting email."""
    user = update.message.from_user
    
    # Check if user is awaiting email input for free lesson registration
    if context.user_data.get('awaiting_free_lesson_email', False):
        await handle_email_input(update, context)
        return
    
    # Check if user has any active booking (pending, uploaded, or approved)
    booking_record = db_bookings.get_active_booking_by_user(user.id)
    
    if not booking_record:
        # User doesn't have active booking, ignore the message
        return
    
    booking_id = booking_record['id']
    course_id = booking_record['course_id']
    booking_status = booking_record['status']
    course_stream = booking_record.get('course_stream', '4th_stream')
    course_name = booking_record.get('course_name', "Неизвестный курс")
    
    # Log the event with appropriate type based on booking status
    event_type = 'student_response' if booking_status == 2 else 'alternative_payment_proof'
    
    db_events.log_event(
        user.id, 
        event_type,
        username=user.username,
        first_name=user.first_name,
        details={
            'message_type': update.message.effective_attachment.__class__.__name__ if update.message.effective_attachment else 'text',
            'booking_status': booking_status,
            'message_text': update.message.text if update.message.text else None
        }
    )
    
    logger.info(f"Message received from user {user.id} ({user.first_name}) with booking {booking_id}, status: {booking_status}")
    
    # Update booking status only if it's pending (0)
    if booking_status == 0:
        if not db_bookings.update_booking_status(booking_id, 1):
            await update.message.reply_text("Произошла ошибка при обновлении статуса заявки.")
            return
        logger.info(f"Booking {booking_id} for user {user.id} updated to 'payment uploaded' status (1).")
        
        # Notify user about payment check
        await update.message.reply_text(
            rf"📨 Сообщение получено для заявки №*{escape_markdown_v2(str(booking_id))}* "
            rf"\(курс '*{escape_markdown_v2(course_name)}*'\)\."
            r"\nМы проверим вашу оплату и сообщим о результате\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    elif booking_status == 2:
        # User is already approved, just acknowledge their response
        await update.message.reply_text(
            rf"👍 Спасибо за ответ\\! Ваше сообщение получено\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    if config.TARGET_CHAT_ID == 0:
        logger.error("TARGET_CHAT_ID is not set. Cannot forward message to admin.")
        return
    
    # Forward the message to admin
    forwarded_message = await context.bot.forward_message(
        chat_id=config.TARGET_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    
    # Send admin notification with different caption based on status
    if booking_status == 2:
        # Student response after approval
        caption_for_admin = _build_admin_notification_caption(user, booking_record, 'student_response', '✅ Оплачено')
        # No approve button for already approved bookings
        await context.bot.send_message(
            chat_id=config.TARGET_CHAT_ID,
            text=caption_for_admin,
            reply_to_message_id=forwarded_message.message_id,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        # Payment confirmation or alternative proof
        status_text = "⏳ Ожидает проверки" if booking_status == 1 else "📝 Новая заявка"
        caption_for_admin = _build_admin_notification_caption(user, booking_record, 'alternative_payment', status_text)
        
        admin_keyboard = [[
            InlineKeyboardButton(
                f"✅ Одобрить ({booking_id})",
                callback_data=f"{CALLBACK_ADMIN_APPROVE_PAYMENT}{user.id}_{booking_id}"
            )
        ]]
        
        await context.bot.send_message(
            chat_id=config.TARGET_CHAT_ID,
            text=caption_for_admin,
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            reply_to_message_id=forwarded_message.message_id,
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def handle_email_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles email input for free lesson registration."""
    user = update.message.from_user
    
    # Проверяем, что это текстовое сообщение
    if not update.message.text:
        await update.message.reply_text(
            "Пожалуйста, отправьте ваш email адрес текстовым сообщением.",
            parse_mode='HTML'
        )
        return
    
    email = update.message.text.strip()
    
    # Валидируем email
    if not db_free_lessons.validate_email(email):
        await update.message.reply_text(
            get_text("FREE_LESSON", "EMAIL_INVALID"),
            parse_mode='HTML'
        )
        return
    
    # Получаем lesson_type из context или используем fallback
    lesson_type = context.user_data.get('pending_lesson_type', 'cursor_lesson')
    lesson_data = get_lesson_by_type(lesson_type)
    
    # Извлекаем дату урока из lesson_data
    lesson_date = None
    if lesson_data and 'datetime' in lesson_data:
        lesson_datetime = lesson_data['datetime']
        if lesson_datetime:
            lesson_date = lesson_datetime.date()  # Извлекаем только дату из datetime объекта
    
    # Создаём регистрацию с указанием lesson_type и lesson_date
    registration_id = db_free_lessons.create_free_lesson_registration(
        user.id,
        user.username,
        user.first_name,
        email,
        lesson_type=lesson_type,
        lesson_date=lesson_date
    )
    
    if registration_id:
        # Успешная регистрация
        # Сбрасываем состояние
        context.user_data.pop('awaiting_free_lesson_email', None)
        context.user_data.pop('pending_lesson_type', None)
        
        # Логируем успешную регистрацию
        db_events.log_event(
            user.id, 
            'free_lesson_registered',
            details={'email': email, 'registration_id': registration_id, 'lesson_type': lesson_type},
            username=user.username,
            first_name=user.first_name
        )
        
        # Формируем сообщение об успешной регистрации
        if lesson_data:
            date_info = lesson_data.get('date_text', 'информация о дате будет отправлена дополнительно')
        else:
            date_info = 'информация о дате будет отправлена дополнительно'
        
        success_message = get_text("FREE_LESSON", "REGISTRATION_SUCCESS").format(
            date=date_info,
            email=email
        )
        
        await update.message.reply_text(success_message, parse_mode='HTML')
        logger.info(f"User {user.id} successfully registered for free lesson with email {email}")
    else:
        # Ошибка регистрации
        await update.message.reply_text(
            "Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.",
            parse_mode='HTML'
        )
        logger.error(f"Failed to register user {user.id} for free lesson with email {email}")