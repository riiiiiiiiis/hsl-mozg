import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
import constants
from utils import escape_markdown_v2
from db import courses as db_courses
from db import bookings as db_bookings
from db import events as db_events
from db import referrals as db_referrals

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
        await query.edit_message_text(f"✅ Оплата для заявки №{booking_id} (Пользователь {target_user_id}) ПОДТВЕРЖДЕНА.")
        
        booking_details = db_bookings.get_booking_details(booking_id)
        is_consultation = False # Placeholder, add logic if consultation courses exist
        if booking_details:
            # Example: check if course ID corresponds to a consultation
            # is_consultation = booking_details['course_id'] in [3, 4]
            pass

        confirmation_text = f"🎉 Поздравляем! Ваша оплата по заявке №{booking_id} подтверждена. Место забронировано!"
        if is_consultation:
            confirmation_text += f"\n\nПожалуйста, выберите время для консультации: {constants.CALENDAR_LINK}"
        
        await context.bot.send_message(chat_id=target_user_id, text=confirmation_text)
    else:
        await query.edit_message_text(f"⚠️ Не удалось подтвердить заявку №{booking_id}. Возможно, она уже обработана.")