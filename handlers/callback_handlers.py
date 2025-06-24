import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
import constants
import database
from utils import escape_markdown_v2

logger = logging.getLogger(__name__)

def get_course_details_text_and_markup(user_first_name, course, referral_info):
    """Helper function to generate the text and keyboard for the course details view."""
    price_info = ""
    if referral_info:
        discount = referral_info['discount_percent']
        discounted_price = course['price_usd'] * (1 - discount / 100)
        price_info = (f"\n💰 Стоимость: <s>${course['price_usd']}</s> "
                      f"<b>${discounted_price:.0f}</b> (скидка {discount}%)\n")
    else:
        price_info = f"\n💰 Стоимость: <b>${course['price_usd']}</b>\n"

    # Simple formatting for the description
    formatted_description = course['description'].replace(
        'На этом курсе', '<b>На этом курсе</b>', 1
    ).replace(
        'После обучения', '<b>После обучения</b>', 1
    )

    text = (
        f"<b>Курс:</b> {course['name']}\n"
        f"<b>Имя:</b> {user_first_name}\n"
        f"<b>Дата старта:</b> 30 мая\n"
        f"{price_info}\n"
        f"{formatted_description}"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Забронировать место", callback_data=constants.CALLBACK_CONFIRM_COURSE_SELECTION)],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
    ]
    return text, InlineKeyboardMarkup(keyboard)


async def main_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main router for all callback queries."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    # Store user info in context for easy access
    context.user_data['user_id'] = user.id
    context.user_data['username'] = user.username or ""
    context.user_data['first_name'] = user.first_name or "Пользователь"

    if data == constants.CALLBACK_RESERVE_SPOT:
        await handle_reserve_spot(query, context)
    elif data == "back_to_start":
        await handle_back_to_start(query, context)
    elif data == constants.CALLBACK_CONFIRM_COURSE_SELECTION:
        await handle_confirm_selection(query, context)
    elif data.startswith(constants.CALLBACK_CANCEL_RESERVATION):
        await handle_cancel_reservation(query, context)
    elif data.startswith(constants.CALLBACK_ADMIN_APPROVE_PAYMENT):
        await handle_admin_approve(query, context)
    else:
        logger.warning(f"Unhandled callback data: {data} from user {user.id}")

async def handle_reserve_spot(query, context):
    """Shows details for the one and only course."""
    course = constants.COURSES[0]
    context.user_data['pending_course_id'] = course['id']
    text, markup = get_course_details_text_and_markup(
        context.user_data['first_name'],
        course,
        context.user_data.get('pending_referral_info')
    )
    await query.edit_message_text(text, reply_markup=markup, parse_mode='HTML', disable_web_page_preview=True)

async def handle_back_to_start(query, context):
    """Returns the user to the initial start message."""
    keyboard = [[InlineKeyboardButton("Посмотреть программу", callback_data=constants.CALLBACK_RESERVE_SPOT)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Привет! Добро пожаловать в школу HashSlash! 👋\n\n...", # Abridged for brevity
        reply_markup=reply_markup
    )

async def handle_confirm_selection(query, context):
    """Confirms course selection and creates a preliminary booking."""
    user_id = context.user_data['user_id']
    course_id = context.user_data.get('pending_course_id')

    if not course_id:
        await query.edit_message_text("Произошла ошибка. Пожалуйста, выберите курс заново.")
        return

    course = next((c for c in constants.COURSES if c["id"] == course_id), None)
    
    referral_code = context.user_data.get('pending_referral_code')
    referral_info = context.user_data.get('pending_referral_info')
    discount_percent = referral_info['discount_percent'] if referral_info else 0

    booking_id = database.create_booking(
        user_id,
        context.user_data['username'],
        context.user_data['first_name'],
        course['name'],
        course['id'],
        referral_code,
        discount_percent
    )

    if not booking_id:
        await query.edit_message_text("Не удалось создать бронирование. Попробуйте снова.")
        return

    logger.info(f"Booking {booking_id} created for user {user_id}")
    
    if referral_info:
        database.apply_referral_discount(referral_info['id'], user_id, booking_id)

    discounted_price_usd = course['price_usd'] * (1 - discount_percent / 100)
    price_rub = round(discounted_price_usd * config.USD_TO_RUB_RATE, 2)
    price_kzt = round(discounted_price_usd * config.USD_TO_KZT_RATE, 2)

    esc_course_name = escape_markdown_v2(course['name'])
    esc_booking_id = escape_markdown_v2(str(booking_id))
    esc_notice = escape_markdown_v2(constants.BOOKING_DURATION_NOTICE)
    
    message_text = (
        f"📝 Ваше место на курс '*{esc_course_name}*' предварительно забронировано \(Заявка №*{esc_booking_id}*\)\.\n\n"
        f"⏳ _{esc_notice}_\n\n"
        f"💳 *Реквизиты для оплаты:*\n"
        f"🇷🇺 Т\-Банк \(RUB\): `{escape_markdown_v2(f'{price_rub:.2f} RUB')}`\n"
        f"🇰🇿 Kaspi \(KZT\): `{escape_markdown_v2(f'{price_kzt:.2f} KZT')}`\n\n"
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

    # To avoid complex logic, we'll just send them back to the start.
    if database.update_booking_status(booking_id, -1):
        logger.info(f"User {user_id} cancelled booking {booking_id}")
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

    if database.update_booking_status(booking_id, 2):
        logger.info(f"Admin {query.from_user.id} approved payment for booking {booking_id}")
        await query.edit_message_text(f"✅ Оплата для заявки №{booking_id} (Пользователь {target_user_id}) ПОДТВЕРЖДЕНА.")
        
        booking_details = database.get_booking_details(booking_id)
        is_consultation = booking_details and booking_details['course_id'] in ["3", "4"]

        confirmation_text = f"🎉 Поздравляем! Ваша оплата по заявке №{booking_id} подтверждена. Место забронировано!"
        if is_consultation:
            confirmation_text += f"\n\nПожалуйста, выберите время для консультации: {constants.CALENDAR_LINK}"
        
        await context.bot.send_message(chat_id=target_user_id, text=confirmation_text)
    else:
        await query.edit_message_text(f"⚠️ Не удалось подтвердить заявку №{booking_id}. Возможно, она уже обработана.")