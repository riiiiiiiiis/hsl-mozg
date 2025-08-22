import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
import constants
from utils import escape_markdown_v2, get_approval_timestamp
from db import courses as db_courses
from db import bookings as db_bookings
from db import events as db_events
from db import referrals as db_referrals
from db import free_lessons as db_free_lessons

logger = logging.getLogger(__name__)

async def main_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main router for all callback queries."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    context.user_data['user_id'] = user.id
    context.user_data['username'] = user.username or ""
    context.user_data['first_name'] = user.first_name or "Пользователь"

    if data.startswith(constants.CALLBACK_SELECT_COURSE_PREFIX):
        await handle_select_course(query, context)
    elif data == constants.CALLBACK_CONFIRM_COURSE_SELECTION:
        await handle_confirm_selection(query, context)
    elif data.startswith(constants.CALLBACK_CANCEL_RESERVATION):
        await handle_cancel_reservation(query, context)
    elif data.startswith(constants.CALLBACK_ADMIN_APPROVE_PAYMENT):
        await handle_admin_approve(query, context)
    elif data.startswith(constants.CALLBACK_FREE_LESSON_REGISTER_PREFIX):
        await handle_free_lesson_register_by_id(query, context)
    elif data.startswith(constants.CALLBACK_FREE_LESSON_PREFIX):
        await handle_free_lesson_by_id(query, context)
    # Legacy handlers (deprecated but kept for backward compatibility)
    elif data == constants.CALLBACK_FREE_LESSON_INFO if hasattr(constants, 'CALLBACK_FREE_LESSON_INFO') else False:
        await handle_free_lesson_info(query, context)
    elif data == constants.CALLBACK_FREE_LESSON_REGISTER if hasattr(constants, 'CALLBACK_FREE_LESSON_REGISTER') else False:
        await handle_free_lesson_register(query, context)
    else:
        logger.warning(f"Unhandled callback data: {data} from user {user.id}")
        # Логируем неизвестные callback'и
        db_events.log_event(
            user.id, 
            'unknown_callback', 
            details={'callback_data': data},
            username=context.user_data['username'],
            first_name=context.user_data['first_name']
        )

async def handle_select_course(query, context):
    """Shows details for a dynamically selected course."""
    try:
        course_id = int(query.data.replace(constants.CALLBACK_SELECT_COURSE_PREFIX, ''))
    except (ValueError, IndexError):
        logger.error(f"Invalid course callback data: {query.data}")
        return

    course = db_courses.get_course_by_id(course_id)
    if not course:
        await query.edit_message_text("Извините, этот курс больше не доступен.")
        return

    context.user_data['pending_course_id'] = course_id
    db_events.log_event(
        query.from_user.id, 
        'view_program', 
        details={'course_id': course_id},
        username=context.user_data['username'],
        first_name=context.user_data['first_name']
    )

    price_usd = course['price_usd_cents'] / 100
    referral_info = context.user_data.get('pending_referral_info')
    
    price_info_str = f"<b>${price_usd:.0f}</b>"
    if referral_info:
        discount = referral_info['discount_percent']
        discounted_price = price_usd * (1 - discount / 100)
        price_info_str = f"<s>${price_usd:.0f}</s> <b>${discounted_price:.0f}</b> (скидка {discount}%)"

    text = (
        f"<b>Курс:</b> {course['name']}\n"
        f"<b>Имя:</b> {context.user_data['first_name']}\n"
        f"<b>Старт:</b> {course['start_date_text']}\n"
        f"<b>Стоимость:</b> {price_info_str}\n\n"
        f"{course['description']}"
    )
    
    keyboard = [[InlineKeyboardButton("✅ Забронировать место", callback_data=constants.CALLBACK_CONFIRM_COURSE_SELECTION)]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML', disable_web_page_preview=True)

async def handle_confirm_selection(query, context):
    """Confirms course selection and creates a preliminary booking."""
    user_id = context.user_data['user_id']
    course_id = context.user_data.get('pending_course_id')

    if not course_id:
        await query.edit_message_text("Произошла ошибка, сессия истекла. Пожалуйста, начните заново с /start.")
        return

    course = db_courses.get_course_by_id(course_id)
    referral_code = context.user_data.get('pending_referral_code')
    referral_info = context.user_data.get('pending_referral_info')
    discount_percent = referral_info['discount_percent'] if referral_info else 0

    booking_id = db_bookings.create_booking(
        user_id,
        context.user_data['username'],
        context.user_data['first_name'],
        course_id,
        referral_code,
        discount_percent
    )

    if not booking_id:
        await query.edit_message_text("Не удалось создать бронирование. Пожалуйста, попробуйте снова.")
        return

    db_events.log_event(
        user_id, 
        'booking_created', 
        details={'course_id': course_id, 'booking_id': booking_id},
        username=context.user_data['username'],
        first_name=context.user_data['first_name']
    )
    if referral_info:
        db_referrals.apply_referral_discount(referral_info['id'], user_id, booking_id)

    price_usd = course['price_usd_cents'] / 100
    discounted_price_usd = price_usd * (1 - discount_percent / 100)
    
    price_rub = round(discounted_price_usd * config.USD_TO_RUB_RATE, 2)
    price_kzt = round(discounted_price_usd * config.USD_TO_KZT_RATE, 2)
    price_ars = round(discounted_price_usd * config.USD_TO_ARS_RATE, 2)

    esc_course_name = escape_markdown_v2(course['name'])
    esc_booking_id = escape_markdown_v2(str(booking_id))
    esc_notice = escape_markdown_v2(constants.BOOKING_DURATION_NOTICE)
    
    # Экранируем реквизиты для безопасного отображения
    esc_tbank_card = escape_markdown_v2(config.TBANK_CARD_NUMBER)
    esc_tbank_holder = escape_markdown_v2(config.TBANK_CARD_HOLDER)
    esc_kaspi_card = escape_markdown_v2(config.KASPI_CARD_NUMBER)
    esc_ars_alias = escape_markdown_v2(config.ARS_ALIAS)
    esc_usdt_address = escape_markdown_v2(config.USDT_TRC20_ADDRESS)
    
    message_text = (
        f"📝 Ваше место на курс '*{esc_course_name}*' предварительно забронировано \(Заявка №*{esc_booking_id}*\)\.\n\n"
        f"⏳ _{esc_notice}_\n\n"
        f"💳 *Реквизиты для оплаты:*\n\n"
        f"🇷🇺 *Т\-Банк \({escape_markdown_v2(f'{price_rub:.2f} RUB')}\):*\n"
        f"  Карта: `{esc_tbank_card}`\n"
        f"  Получатель: {esc_tbank_holder}\n\n"
        f"🇰🇿 *Kaspi \({escape_markdown_v2(f'{price_kzt:.2f} KZT')}\):*\n"
        f"  Карта: `{esc_kaspi_card}`\n\n"
        f"🇦🇷 *Аргентина \({escape_markdown_v2(f'{price_ars:.2f} ARS')}\):*\n"
        f"  Alias: `{esc_ars_alias}`\n\n"
        f"💸 *USDT TRC\-20 \({escape_markdown_v2(f'{discounted_price_usd:.2f} USDT')}\):*\n"
        f"  Адрес: `{esc_usdt_address}`\n\n"
        f"🧾 После оплаты отправьте фото чека в этот чат\."
    )

    keyboard = [[InlineKeyboardButton("❌ Отменить бронь", callback_data=f"{constants.CALLBACK_CANCEL_RESERVATION}_{booking_id}")]]
    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN_V2)

async def handle_cancel_reservation(query, context):
    """Handles cancellation of a pending reservation."""
    try:
        booking_id = int(query.data.split('_')[-1])
        user_id = context.user_data['user_id']
    except (ValueError, IndexError):
        logger.error(f"Invalid cancel callback data: {query.data}")
        return

    if db_bookings.update_booking_status(booking_id, -1):
        logger.info(f"User {user_id} cancelled booking {booking_id}")
        # Логируем отмену бронирования
        db_events.log_event(
            user_id, 
            'booking_cancelled', 
            details={'booking_id': booking_id},
            username=context.user_data['username'],
            first_name=context.user_data['first_name']
        )
        await query.edit_message_text("Ваше бронирование отменено. Вы можете начать заново, нажав /start.")
    else:
        await query.edit_message_text("Не удалось отменить бронирование. Возможно, оно уже обработано.")

async def handle_admin_approve(query, context):
    """Handles an admin approving a payment."""
    try:
        parts = query.data.split('_')
        target_user_id = int(parts[-2])
        booking_id = int(parts[-1])
    except (ValueError, IndexError):
        logger.error(f"Invalid admin approve callback: {query.data}")
        return

    if db_bookings.update_booking_status(booking_id, 2):
        logger.info(f"Admin {query.from_user.id} approved payment for booking {booking_id}")
        # Логируем подтверждение админом
        db_events.log_event(
            target_user_id, 
            'payment_approved', 
            details={'booking_id': booking_id, 'approved_by': query.from_user.id},
            username=None,  # username цели получим из bookings
            first_name=None
        )
        
        # Preserve original message content and append approval status
        try:
            # First, remove the inline keyboard while keeping the content
            await query.edit_message_reply_markup(reply_markup=None)
            
            # Then append approval status to the original message
            original_text = query.message.text or query.message.caption or ""
            approval_timestamp = get_approval_timestamp()
            approval_status = f"\n\n✅ ОДОБРЕНО - {approval_timestamp}"
            
            # Update message with appended approval status
            updated_text = original_text + approval_status
            
            # Try to edit the message text/caption
            if query.message.text:
                await query.edit_message_text(updated_text)
            elif query.message.caption:
                await query.edit_message_caption(caption=updated_text)
            else:
                # Fallback: send a new message if we can't edit
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"✅ Оплата для заявки №{booking_id} (Пользователь {target_user_id}) ПОДТВЕРЖДЕНА. {approval_timestamp}"
                )
                
        except Exception as e:
            logger.warning(f"Failed to preserve message content for booking {booking_id}: {e}")
            # Fallback to current behavior
            try:
                await query.edit_message_text(f"✅ Оплата для заявки №{booking_id} (Пользователь {target_user_id}) ПОДТВЕРЖДЕНА.")
            except Exception as fallback_error:
                logger.error(f"Fallback message edit also failed for booking {booking_id}: {fallback_error}")
        
        booking_details = db_bookings.get_booking_details(booking_id)
        is_consultation = False # Placeholder, add logic if consultation courses exist
        if booking_details:
            # Example: check if course ID corresponds to a consultation
            # is_consultation = booking_details['course_id'] in [3, 4]
            pass

        # Получаем информацию о пользователе для персонализации
        user_first_name = booking_details.get('first_name', 'Друг') if booking_details else 'Друг'
        
        confirmation_text = f"""Привет, {user_first_name}!

Ты в Потоке BOCTOK (13, 20, 27 августа и 3 сентября).

Что дальше:
1. 13 августа в 21:00 по мск - первый лайв: https://calendar.app.google/AcavEBkN1ZTMsQ1q6
2. Вступай в группу потока: https://t.me/+oxpLHOBteD41ZThi

По любым вопросам пиши @serejaris
"""
        
        if is_consultation:
            confirmation_text += f"\n\nПожалуйста, выберите время для консультации: {constants.CALENDAR_LINK}"
        
        # Отправляем фото с текстом
        photo_file_id = "AgACAgIAAxkBAAE5FuNolBevwD24uQRSmq28gsyV6FWTnQACdvsxG81-oUhX08cmOnTLeQEAAwIAA3kAAzYE"
        await context.bot.send_photo(
            chat_id=target_user_id, 
            photo=photo_file_id,
            caption=confirmation_text
        )
    else:
        await query.edit_message_text(f"⚠️ Не удалось подтвердить заявку №{booking_id}. Возможно, она уже обработана.")

async def handle_free_lesson_info(query, context):
    """Shows information about the free lesson."""
    user_id = context.user_data['user_id']
    
    # Логируем просмотр информации о бесплатном уроке
    db_events.log_event(
        user_id, 
        'free_lesson_info_viewed',
        username=context.user_data['username'],
        first_name=context.user_data['first_name']
    )
    
    # Проверяем, зарегистрирован ли пользователь на текущий урок (cursor_lesson)
    is_registered = db_free_lessons.is_user_registered_for_lesson_type(user_id, 'cursor_lesson')
    
    text = (
        f"<b>{constants.FREE_LESSON['title']}</b>\n\n"
        f"📅 <b>Дата:</b> {constants.FREE_LESSON['date_text']}\n\n"
        f"{constants.FREE_LESSON['description']}"
    )
    
    keyboard = []
    if is_registered:
        # Если уже зарегистрирован на текущий урок, показываем соответствующее сообщение
        registration = db_free_lessons.get_registration_by_user_and_type(user_id, 'cursor_lesson')
        text += f"\n\n✅ <b>Вы уже зарегистрированы!</b>\n📧 Email: {registration['email']}\n🔔 Ссылка будет отправлена за 15 минут до начала."
    else:
        # Если не зарегистрирован на текущий урок, показываем кнопку регистрации
        keyboard.append([InlineKeyboardButton("📝 Записаться на урок", callback_data=constants.CALLBACK_FREE_LESSON_REGISTER)])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)

async def handle_free_lesson_register(query, context):
    """Initiates free lesson registration process."""
    user_id = context.user_data['user_id']
    
    # Проверяем, не зарегистрирован ли пользователь уже на текущий урок (cursor_lesson)
    if db_free_lessons.is_user_registered_for_lesson_type(user_id, 'cursor_lesson'):
        registration = db_free_lessons.get_registration_by_user_and_type(user_id, 'cursor_lesson')
        message = constants.FREE_LESSON_ALREADY_REGISTERED.format(
            date=constants.FREE_LESSON['date_text']
        )
        await query.edit_message_text(message, parse_mode='HTML')
        return
    
    # Устанавливаем состояние ожидания email
    context.user_data['awaiting_free_lesson_email'] = True
    
    # Логируем начало регистрации
    db_events.log_event(
        user_id, 
        'free_lesson_registration_started',
        username=context.user_data['username'],
        first_name=context.user_data['first_name']
    )
    
    await query.edit_message_text(constants.FREE_LESSON_EMAIL_REQUEST, parse_mode='HTML')


async def handle_free_lesson_by_id(query, context):
    """Shows information about a specific lesson by ID"""
    logger.info(f"DEBUG: handle_free_lesson_by_id called with callback: '{query.data}'")
    
    try:
        raw_id_str = query.data.replace(constants.CALLBACK_FREE_LESSON_PREFIX, '')
        lesson_id = int(raw_id_str)
        logger.info(f"DEBUG: Successfully parsed lesson_id: {lesson_id} from '{query.data}'")
    except ValueError:
        logger.error(f"ERROR: Failed to parse lesson_id from callback '{query.data}'")
        await query.edit_message_text("Ошибка: неверный ID урока")
        return
    
    lesson_type, lesson_data = constants.get_lesson_by_id(lesson_id)
    if not lesson_data:
        await query.edit_message_text("Урок не найден")
        return
    
    user_id = context.user_data['user_id']
    
    # Логируем просмотр информации о конкретном уроке
    db_events.log_event(
        user_id, 
        'free_lesson_info_viewed',
        details={'lesson_type': lesson_type, 'lesson_id': lesson_id},
        username=context.user_data['username'],
        first_name=context.user_data['first_name']
    )
    
    # Проверяем, зарегистрирован ли пользователь на этот конкретный урок
    is_registered = db_free_lessons.is_user_registered_for_lesson_type(user_id, lesson_type)
    
    text = f"<b>{lesson_data['title']}</b>\n\n{lesson_data['description']}"
    
    keyboard = []
    if is_registered:
        message = constants.FREE_LESSON_ALREADY_REGISTERED.format(
            date=lesson_data['description']  # Description contains the date and all info
        )
        await query.edit_message_text(message, parse_mode='HTML')
    else:
        register_callback = f"{constants.CALLBACK_FREE_LESSON_REGISTER_PREFIX}{lesson_id}"
        logger.info(f"DEBUG: Creating register button with callback: '{register_callback}' (lesson_id: {lesson_id})")
        keyboard.append([InlineKeyboardButton("📝 Записаться", callback_data=register_callback)])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


async def handle_free_lesson_register_by_id(query, context):
    """Starts registration process for a specific lesson by ID"""
    # Детальное логирование для диагностики
    logger.info(f"DEBUG: Raw callback data: '{query.data}'")
    logger.info(f"DEBUG: Expected prefix: '{constants.CALLBACK_FREE_LESSON_REGISTER_PREFIX}'")
    
    try:
        # Логируем процесс парсинга
        raw_id_str = query.data.replace(constants.CALLBACK_FREE_LESSON_REGISTER_PREFIX, '')
        logger.info(f"DEBUG: After prefix removal: '{raw_id_str}'")
        
        lesson_id = int(raw_id_str)
        logger.info(f"DEBUG: Parsed lesson_id: {lesson_id}")
        
    except ValueError as e:
        logger.error(f"ERROR: Failed to parse lesson_id from callback '{query.data}': {e}")
        await query.edit_message_text(f"Ошибка: неверный ID урока. Данные: {query.data}")
        return
    
    lesson_type, lesson_data = constants.get_lesson_by_id(lesson_id)
    logger.info(f"DEBUG: Lesson lookup result - lesson_type: {lesson_type}, lesson_data: {lesson_data is not None}")
    
    if not lesson_data:
        logger.error(f"ERROR: Lesson with ID {lesson_id} not found in constants")
        await query.edit_message_text(f"Урок не найден (ID: {lesson_id})")
        return
    
    # Проверяем, что урок еще не прошел (с учетом grace period)
    from datetime import datetime, timedelta, timezone
    lesson_datetime = lesson_data.get('datetime')
    if lesson_datetime:
        # Используем timezone-aware datetime для сравнения
        current_time = datetime.now(timezone.utc)
        
        # Преобразуем lesson_datetime в UTC если у него есть временная зона
        if lesson_datetime.tzinfo is None:
            # Если нет временной зоны, считаем что это UTC
            lesson_datetime = lesson_datetime.replace(tzinfo=timezone.utc)
        else:
            # Конвертируем в UTC для сравнения
            lesson_datetime = lesson_datetime.astimezone(timezone.utc)
        
        grace_period = timedelta(hours=2)
        if current_time > lesson_datetime + grace_period:
            await query.edit_message_text(
                "🕐 К сожалению, этот воркшоп уже прошел.\n\n"
                "Следите за новыми мероприятиями в нашем боте!",
                parse_mode='HTML'
            )
            return
    
    user_id = context.user_data['user_id']
    
    # Проверяем, не записан ли пользователь уже на этот урок
    if db_free_lessons.is_user_registered_for_lesson_type(user_id, lesson_type):
        message = constants.FREE_LESSON_ALREADY_REGISTERED.format(
            date=lesson_data.get('date_text', 'Дата уточняется')  # Use date_text field instead of full description
        )
        await query.edit_message_text(message, parse_mode='HTML')
        return
    
    # Сохраняем lesson_type для последующей регистрации
    context.user_data['pending_lesson_type'] = lesson_type
    context.user_data['awaiting_free_lesson_email'] = True
    
    # Логируем начало регистрации на конкретный урок
    db_events.log_event(
        user_id, 
        'free_lesson_registration_started',
        details={'lesson_type': lesson_type, 'lesson_id': lesson_id},
        username=context.user_data['username'],
        first_name=context.user_data['first_name']
    )
    
    await query.edit_message_text(constants.FREE_LESSON_EMAIL_REQUEST, parse_mode='HTML')