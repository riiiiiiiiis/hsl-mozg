import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
import constants
from utils import escape_markdown_v2, get_user_identification, get_course_flow_info
from db import bookings as db_bookings
from db import events as db_events
from db import free_lessons as db_free_lessons

logger = logging.getLogger(__name__)

def get_start_date_for_course(course_id):
    """Get start date text for a course from constants."""
    for course in constants.COURSES:
        if course['id'] == course_id:
            return course.get('start_date_text', 'дата не указана')
    return 'дата не указана'

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
    
    # Get course ID for start date lookup
    course_id = None
    for course in constants.COURSES:
        if course['name'] == course_name:
            course_id = course['id']
            break
    
    # Get start date and format course flow info
    start_date_text = get_start_date_for_course(course_id) if course_id else 'дата не указана'
    course_flow_info = get_course_flow_info(course_stream, start_date_text)

    if not db_bookings.update_booking_status(booking_id, 1):
        await update.message.reply_text("Произошла ошибка при обновлении статуса заявки.")
        return

    logger.info(f"Booking {booking_id} for user {user.id} updated to 'payment uploaded' status (1).")

    await update.message.reply_text(
        f"🙏 Спасибо, {escape_markdown_v2(user.first_name)}\! Ваше фото для заявки №*{escape_markdown_v2(str(booking_id))}* "
        f"\(курс '*{escape_markdown_v2(course_name)}*' \) получено\.\n"
        "Оплата проверяется\. Мы сообщим вам о результате\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    if config.TARGET_CHAT_ID == 0:
        logger.error("TARGET_CHAT_ID is not set. Cannot forward photo to admin.")
        return

    # Enhanced user identification
    user_identification = get_user_identification({
        'username': user.username,
        'first_name': user.first_name,
        'user_id': user.id
    })

    caption_for_admin = (
        f"🧾 *Новый чек для проверки\!*\n"
        f"Пользователь: {escape_markdown_v2(user_identification)} \(ID: `{user.id}`\)\n"
        f"Заявка №: *{escape_markdown_v2(str(booking_id))}*\n"
        f"Курс: *{escape_markdown_v2(course_name)}*\n"
        f"Поток: *{escape_markdown_v2(course_flow_info)}*"
    )

    forwarded_message = await context.bot.forward_message(
        chat_id=config.TARGET_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )

    admin_keyboard = [[
        InlineKeyboardButton(
            f"✅ Одобрить ({booking_id})",
            callback_data=f"{constants.CALLBACK_ADMIN_APPROVE_PAYMENT}{user.id}_{booking_id}"
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
    
    # Get start date and format course flow info
    start_date_text = get_start_date_for_course(course_id)
    course_flow_info = get_course_flow_info(course_stream, start_date_text)
    
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
            f"📨 Сообщение получено для заявки №*{escape_markdown_v2(str(booking_id))}* "
            f"\(курс '*{escape_markdown_v2(course_name)}*'\)\."
            "\nМы проверим вашу оплату и сообщим о результате\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    elif booking_status == 2:
        # User is already approved, just acknowledge their response
        await update.message.reply_text(
            f"👍 Спасибо за ответ\\! Ваше сообщение получено\\.",
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
    
    # Enhanced user identification
    user_identification = get_user_identification({
        'username': user.username,
        'first_name': user.first_name,
        'user_id': user.id
    })

    # Send admin notification with different caption based on status
    if booking_status == 2:
        # Student response after approval
        caption_for_admin = (
            f"💬 *Ответ студента*\n"
            f"Пользователь: {escape_markdown_v2(user_identification)} \(ID: `{user.id}`\)\n"
            f"Заявка №: *{escape_markdown_v2(str(booking_id))}*\n"
            f"Курс: *{escape_markdown_v2(course_name)}*\n"
            f"Поток: *{escape_markdown_v2(course_flow_info)}*\n"
            f"Статус: ✅ Оплачено"
        )
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
        caption_for_admin = (
            f"📩 *Альтернативное подтверждение оплаты\!*\n"
            f"Пользователь: {escape_markdown_v2(user_identification)} \(ID: `{user.id}`\)\n"
            f"Заявка №: *{escape_markdown_v2(str(booking_id))}*\n"
            f"Курс: *{escape_markdown_v2(course_name)}*\n"
            f"Поток: *{escape_markdown_v2(course_flow_info)}*\n"
            f"Статус: {escape_markdown_v2(status_text)}"
        )
        
        admin_keyboard = [[
            InlineKeyboardButton(
                f"✅ Одобрить ({booking_id})",
                callback_data=f"{constants.CALLBACK_ADMIN_APPROVE_PAYMENT}{user.id}_{booking_id}"
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
            constants.FREE_LESSON_EMAIL_INVALID,
            parse_mode='HTML'
        )
        return
    
    # Создаём регистрацию
    registration_id = db_free_lessons.create_free_lesson_registration(
        user.id,
        user.username,
        user.first_name,
        email
    )
    
    if registration_id:
        # Успешная регистрация
        # Сбрасываем состояние
        context.user_data.pop('awaiting_free_lesson_email', None)
        
        # Логируем успешную регистрацию
        db_events.log_event(
            user.id, 
            'free_lesson_registered',
            details={'email': email, 'registration_id': registration_id},
            username=user.username,
            first_name=user.first_name
        )
        
        success_message = constants.FREE_LESSON_REGISTRATION_SUCCESS.format(
            date=constants.FREE_LESSON['date_text'],
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