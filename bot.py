import sqlite3
import logging
import sys
from datetime import datetime
import asyncio
import urllib.request
import urllib.error
import random
import string
import config
import referral_config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode # Import ParseMode
from telegram.error import Conflict
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    PicklePersistence,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dedicated logger for course selections
course_selection_logger = logging.getLogger('course_selection')
course_selection_logger.setLevel(logging.INFO)
# Create a file handler for the course selection logger
course_log_handler = logging.FileHandler('course_selection.log')
course_log_handler.setLevel(logging.INFO)
# Create a formatter and set it for the handler
course_log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
course_log_handler.setFormatter(course_log_formatter)
# Add the handler to the logger
course_selection_logger.addHandler(course_log_handler)
course_selection_logger.propagate = False # Prevent logging to root logger as well

BOOKING_DURATION_NOTICE = "Ваше место предварительно забронировано на 1 час. Пожалуйста, произведите оплату и отправьте фото чека в этот чат для подтверждения."

COURSES = [
    {
        "id": "1",
        "button_text": "Вайб Кодинг",
        "name": "Вайб кодинг",
        "price_usd": 150,
        "description": "На этом курсе в течение двух недель я учу превращать идеи в рабочие прототипы. Программируем на русском языке. Наглядно объясняю как работает ИИ, интернет и приложения. Общение в закрытой группе, домашки, три созвона с записями. Поддержка продолжается месяц после курса.\nПосле обучения ты будешь знать как создавать сайты с помощью ИИ, что такое база данных, как собрать телеграм бота за вечер и выложить проект в интернет. Набор промптов в подарок!\nДля кого: вообще для всех\nДлительность: три недели\nФормат: 3 практических лекции по пятницам или средам в 20:00 МСК\nСтоимость: 150$\nСтарт: 30 мая\n\nОплата возможна переводом на карты Т-Банка, Каспи или в USDT на крипто кошелек.\n\nЧто дальше: После оплаты я добавлю тебя в закрытую группу, где мы будем общаться и делиться материалами. Перед стартом курса пришлю всю необходимую информацию."
    }
]

# Constants for calendar link and other URLs
CALENDAR_LINK = "https://calendar.app.google/gYhZNcreyWrAuEgT9"

# Callback constants for course selection correspond to course 'id' or index
CALLBACK_RESERVE_SPOT = "reserve_spot"
CALLBACK_SELECT_COURSE_PREFIX = "select_course_" # Used to identify course selection callbacks
# Individual callbacks like CALLBACK_SELECT_COURSE_1 are still used for clarity in button creation if needed
# but logic will parse ID from callback string like "select_course_1", "select_course_2" etc.
CALLBACK_SELECT_COURSE_1 = "select_course_1"
CALLBACK_SELECT_COURSE_2 = "select_course_2"
CALLBACK_SELECT_COURSE_3 = "select_course_3"
CALLBACK_SELECT_COURSE_4 = "select_course_4"
CALLBACK_CONFIRM_COURSE_SELECTION = "confirm_course_selection_v2"
CALLBACK_BACK_TO_COURSE_SELECTION = "back_to_course_selection"
CALLBACK_ADMIN_APPROVE_PAYMENT = "admin_approve_"
CALLBACK_ADMIN_REJECT_PAYMENT = "admin_reject_"
CALLBACK_CANCEL_RESERVATION = "cancel_reservation"

def escape_markdown_v2(text: str) -> str:
    """Helper function to escape text for MarkdownV2 parsing."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return "".join(f'\\{char}' if char in escape_chars else char for char in str(text))


def get_db_connection():
    conn = sqlite3.connect(config.DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        # Check if the course_id column exists
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'course_id' not in columns:
            # Add course_id column if it doesn't exist
            conn.execute("ALTER TABLE bookings ADD COLUMN course_id TEXT")
            logger.info("Added course_id column to bookings table")
        
        # Check if referral_code column exists
        if 'referral_code' not in columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN referral_code TEXT")
            logger.info("Added referral_code column to bookings table")
        
        if 'discount_percent' not in columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN discount_percent INTEGER DEFAULT 0")
            logger.info("Added discount_percent column to bookings table")
        
        # Check if name column exists in referral_coupons table
        cursor.execute(f"PRAGMA table_info({referral_config.REFERRAL_TABLE_NAME})")
        ref_columns = [column[1] for column in cursor.fetchall()]
        
        if ref_columns and 'name' not in ref_columns:
            conn.execute(f"ALTER TABLE {referral_config.REFERRAL_TABLE_NAME} ADD COLUMN name TEXT")
            logger.info("Added name column to referral_coupons table")
        
        # Create table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                chosen_course TEXT,
                course_id TEXT,
                confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referral_code TEXT,
                discount_percent INTEGER DEFAULT 0,
                UNIQUE(user_id, chosen_course, created_at)
            )
        """)
        
        # Create referral coupons table
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {referral_config.REFERRAL_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT,
                discount_percent INTEGER NOT NULL,
                max_activations INTEGER NOT NULL,
                current_activations INTEGER DEFAULT 0,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Create referral usage tracking table
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {referral_config.REFERRAL_USAGE_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                booking_id INTEGER,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupon_id) REFERENCES {referral_config.REFERRAL_TABLE_NAME}(id),
                FOREIGN KEY (booking_id) REFERENCES bookings(id),
                UNIQUE(coupon_id, user_id)
            )
        """)
        
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database table creation/check error: {e}")
    return conn

def generate_referral_code():
    """Generate a unique referral code"""
    while True:
        code = ''.join(random.choices(referral_config.REFERRAL_CODE_CHARS, k=referral_config.REFERRAL_CODE_LENGTH))
        # Check if code already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM {referral_config.REFERRAL_TABLE_NAME} WHERE code = ?", (code,))
        if not cursor.fetchone():
            conn.close()
            return code
        conn.close()

def validate_referral_code(code, user_id):
    """Validate a referral code and return discount info if valid"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if code exists and is active
    cursor.execute(f"""
        SELECT id, discount_percent, max_activations, current_activations 
        FROM {referral_config.REFERRAL_TABLE_NAME} 
        WHERE code = ? AND is_active = 1
    """, (code,))
    
    coupon = cursor.fetchone()
    if not coupon:
        conn.close()
        return None, "not_found"
    
    # Check if coupon has remaining activations
    if coupon['current_activations'] >= coupon['max_activations']:
        conn.close()
        return None, "expired"
    
    conn.close()
    return {
        'id': coupon['id'],
        'discount_percent': coupon['discount_percent']
    }, "valid"

def apply_referral_discount(coupon_id, user_id, booking_id):
    """Apply referral discount to a booking"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Record usage
        cursor.execute(f"""
            INSERT INTO {referral_config.REFERRAL_USAGE_TABLE_NAME} 
            (coupon_id, user_id, booking_id) VALUES (?, ?, ?)
        """, (coupon_id, user_id, booking_id))
        
        # Increment activation count
        cursor.execute(f"""
            UPDATE {referral_config.REFERRAL_TABLE_NAME} 
            SET current_activations = current_activations + 1 
            WHERE id = ?
        """, (coupon_id,))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error applying referral discount: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_course_selection_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    for course in COURSES:
        keyboard.append([InlineKeyboardButton(course["button_text"], callback_data=f"{CALLBACK_SELECT_COURSE_PREFIX}{course['id']}")])
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    
    # Check if user came with a referral code
    if context.args and len(context.args) > 0:
        start_param = context.args[0]
        if start_param.startswith(referral_config.REFERRAL_START_PARAMETER):
            referral_code = start_param[len(referral_config.REFERRAL_START_PARAMETER):]
            
            # Validate the referral code
            coupon_info, status = validate_referral_code(referral_code, user_id)
            
            if status == "valid":
                # Store the referral code in user context
                context.user_data['pending_referral_code'] = referral_code
                context.user_data['pending_referral_info'] = coupon_info
                
                # Получаем информацию об оставшихся активациях и название
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT name, max_activations, current_activations 
                    FROM {referral_config.REFERRAL_TABLE_NAME} 
                    WHERE id = ?
                """, (coupon_info['id'],))
                coupon_details = cursor.fetchone()
                conn.close()
                
                remaining = coupon_details['max_activations'] - coupon_details['current_activations']
                coupon_name = coupon_details['name']
                
                discount_msg = referral_config.REFERRAL_APPLIED_MESSAGE.format(
                    discount=coupon_info['discount_percent']
                )
                if coupon_name:
                    discount_msg += f"\n🏷️ Купон: {coupon_name}"
                discount_msg += f"\n📊 Осталось активаций: {remaining}"
                
                await update.message.reply_text(discount_msg)
            elif status == "expired" or status == "not_found":
                await update.message.reply_text(referral_config.REFERRAL_EXPIRED_MESSAGE)
    
    keyboard = [[InlineKeyboardButton("Посмотреть программу", callback_data=CALLBACK_RESERVE_SPOT)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        if update.message:
            await update.message.reply_text(
                "Привет! Добро пожаловать в школу HashSlash! 👋\n\n"
                "Меня зовут Сережа, я основатель креативной студии <a href='https://hsl.sh/'> хсл щ</a>. Последние 10 лет я помогаю людям осваивать современные инструменты и технологии.\n\n"
                "Сейчас я открыл набор в группу по <b>вайбкодингу</b>. Вайбкодинг – это новый способ создавать приложения и сайты, не тратя годы на изучение программирования.\n\n"
                "Представьте: вы просто рассказываете искусственному интеллекту (ИИ) на обычном языке, каким должно быть ваше приложение или сайт, а он сам создаёт всё за вас.\n\n"
                "Вы – как режиссёр, который задаёт идею и направление. Вам не нужно разбираться в коде или технических деталях – вы сосредотачиваетесь на том, что делает ваш продукт крутым: его дизайн, удобство и ценность для пользователей.\n\n"
                "Вайбкодинг открывает разработку для всех, кто хочет воплотить свои идеи, даже без технических навыков.",
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Error in start_command: {e}", exc_info=True)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        if query: await query.answer()
        return

    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Error answering callback query for data '{query.data}': {e}", exc_info=True)

    user = query.from_user
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or "Пользователь"

    context.user_data['user_id'] = user_id
    context.user_data['username'] = username
    context.user_data['first_name'] = first_name

    if query.data == CALLBACK_RESERVE_SPOT:
        # Поскольку у нас только один курс, сразу показываем его
        selected_course = COURSES[0]  # Берем первый и единственный курс
        
        chosen_course_name = selected_course["name"]
        course_description = selected_course["description"]
        course_price_usd = selected_course["price_usd"]
        
        context.user_data['pending_course_choice'] = chosen_course_name
        context.user_data['pending_course_id'] = selected_course["id"]
        context.user_data['pending_course_price_usd'] = course_price_usd
        
        # Проверяем, есть ли активная скидка
        referral_info = context.user_data.get('pending_referral_info')
        price_info = ""
        
        if referral_info:
            discount_percent = referral_info['discount_percent']
            discounted_price = course_price_usd * (1 - discount_percent / 100)
            
            price_info = (
                f"\n💰 Стоимость: <s>${course_price_usd}</s> "
                f"<b>${discounted_price:.0f}</b> (скидка {discount_percent}%)\n"
            )
        else:
            price_info = f"\n💰 Стоимость: <b>${course_price_usd}</b>\n"

        # Форматируем описание курса с использованием HTML разметки
        formatted_description = course_description.replace(
            'На этом курсе в течение двух недель я учу превращать идеи в рабочие прототипы.',
            '<b>На этом курсе в течение двух недель я учу превращать идеи в рабочие прототипы.</b>'
        ).replace(
            'После обучения ты будешь знать',
            '<b>После обучения ты будешь знать</b>'
        ).replace(
            'Для кого:',
            '<b>Для кого:</b>'
        ).replace(
            'Длительность:',
            '<b>Длительность:</b>'
        ).replace(
            'Формат:',
            '<b>Формат:</b>'
        ).replace(
            'Стоимость:',
            '<b>Стоимость:</b>'
        ).replace(
            'Старт:',
            '<b>Старт:</b>'
        ).replace(
            'Что дальше:',
            '<b>Что дальше:</b>'
        )
        
        message_text = (
            f"<b>Курс:</b> {chosen_course_name}\n"
            f"<b>Имя:</b> {first_name}\n"
            f"<b>Дата старта:</b> 30 мая\n"
            f"{price_info}\n"
            f"{formatted_description}"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Забронировать место", callback_data=CALLBACK_CONFIRM_COURSE_SELECTION)],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(
                text=message_text, 
                reply_markup=reply_markup, 
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error editing message for course selection confirmation: {e}", exc_info=True)
    
    elif query.data == "back_to_start":
        # Возврат к начальному сообщению
        keyboard = [[InlineKeyboardButton("Посмотреть программу", callback_data=CALLBACK_RESERVE_SPOT)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Привет! Добро пожаловать в школу HashSlash! 👋\n\n"
            "Меня зовут Сережа, я основатель креативной студии hsl sh. Последние 10 лет я помогаю людям осваивать современные инструменты и технологии.\n\n"
            "Сейчас я открыл набор в группу по вайбкодингу. Вайбкодинг – это новый способ создавать приложения и сайты, не тратя годы на изучение программирования.",
            reply_markup=reply_markup
        )

    elif query.data.startswith(CALLBACK_SELECT_COURSE_PREFIX):
        selected_course_id = query.data.replace(CALLBACK_SELECT_COURSE_PREFIX, "")
        selected_course = next((course for course in COURSES if course["id"] == selected_course_id), None)

        if not selected_course:
            logger.warning(f"User {user_id} selected an invalid course ID: {selected_course_id}")
            try:
                await query.edit_message_text(text="Произошла ошибка. Пожалуйста, выберите курс заново.", reply_markup=get_course_selection_keyboard())
            except Exception as e_corr:
                logger.error(f"Error sending correction message for invalid course ID: {e_corr}", exc_info=True)
            return

        chosen_course_name = selected_course["name"]
        course_description = selected_course["description"]
        course_price_usd = selected_course["price_usd"]

        # Log course selection
        try:
            log_message = (
                f"UserID: {user_id} - Username: {username} - FirstName: {first_name} - "
                f"CourseID: {selected_course_id} - CourseName: {chosen_course_name}"
            )
            course_selection_logger.info(log_message)
        except Exception as log_e:
            logger.error(f"Failed to log course selection for user {user_id} (Course: {selected_course_id}): {log_e}", exc_info=True)

        context.user_data['pending_course_choice'] = chosen_course_name
        context.user_data['pending_course_id'] = selected_course_id
        context.user_data['pending_course_price_usd'] = course_price_usd
        
        escaped_course_name = escape_markdown_v2(chosen_course_name)
        escaped_first_name = escape_markdown_v2(first_name)
        escaped_course_description = escape_markdown_v2(course_description)
        
        # Проверяем, есть ли активная скидка
        referral_info = context.user_data.get('pending_referral_info')
        price_info = ""
        
        if referral_info:
            discount_percent = referral_info['discount_percent']
            discounted_price = course_price_usd * (1 - discount_percent / 100)
            
            escaped_original_price = escape_markdown_v2(f"${course_price_usd}")
            escaped_discounted_price = escape_markdown_v2(f"${discounted_price:.0f}")
            escaped_discount = escape_markdown_v2(f"{discount_percent}%")
            
            price_info = (
                f"\n💰 Стоимость: ~{escaped_original_price}~ "
                f"*{escaped_discounted_price}* \(скидка {escaped_discount}\)\n"
            )
        else:
            escaped_price = escape_markdown_v2(f"${course_price_usd}")
            price_info = f"\n💰 Стоимость: *{escaped_price}*\n"

        message_text = (
            f"Вы выбрали курс: *{escaped_course_name}*\n"
            f"Имя: *{escaped_first_name}*\n"
            f"{price_info}\n"
            f"*{escaped_course_description}*\n\n"
            "Подтверждаете свой выбор для предварительного бронирования?"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Да, забронировать", callback_data=CALLBACK_CONFIRM_COURSE_SELECTION)],
            [InlineKeyboardButton("⬅️ Назад (к выбору курса)", callback_data=CALLBACK_BACK_TO_COURSE_SELECTION)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Error editing message for course selection confirmation: {e}", exc_info=True)
    
    elif query.data == CALLBACK_CONFIRM_COURSE_SELECTION:
        current_user_id = context.user_data.get('user_id', user_id)
        current_username = context.user_data.get('username', username)
        current_first_name = context.user_data.get('first_name', first_name)
        chosen_course_name = context.user_data.get('pending_course_choice')
        course_id = context.user_data.get('pending_course_id')
        course_price_usd_val = context.user_data.get('pending_course_price_usd') # Renamed to avoid conflict

        if not chosen_course_name or course_price_usd_val is None:
            logger.warning(f"User {current_user_id} tried to confirm course, but 'pending_course_choice' or 'pending_course_price_usd' not found.")
            try:
                await query.edit_message_text(text="Произошла ошибка. Пожалуйста, выберите курс заново.", reply_markup=get_course_selection_keyboard())
            except Exception as e_corr:
                logger.error(f"Error sending correction message: {e_corr}", exc_info=True)
            return

        conn = None
        booking_id = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check for pending referral discount
            referral_code = context.user_data.get('pending_referral_code')
            referral_info = context.user_data.get('pending_referral_info')
            discount_percent = 0
            
            if referral_code and referral_info:
                discount_percent = referral_info['discount_percent']
            
            cursor.execute(
                """INSERT INTO bookings (user_id, username, first_name, chosen_course, course_id, confirmed, referral_code, discount_percent)
                   VALUES (?, ?, ?, ?, ?, 0, ?, ?)""",
                (current_user_id, current_username, current_first_name, chosen_course_name, course_id, referral_code, discount_percent)
            )
            booking_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Preliminary booking ID {booking_id} for user {current_user_id} ({current_first_name}), course '{chosen_course_name}' saved (status 0). Discount: {discount_percent}%")

            context.user_data[f'booking_id_{current_user_id}'] = booking_id

            # Apply discount if any
            discounted_price_usd = course_price_usd_val
            if discount_percent > 0:
                discounted_price_usd = course_price_usd_val * (1 - discount_percent / 100)
                # Apply the referral discount
                if referral_info:
                    apply_referral_discount(referral_info['id'], current_user_id, booking_id)

            # Calculate payment amounts with discount
            price_kzt = round(discounted_price_usd * config.USD_TO_KZT_RATE, 2)
            price_rub = round(discounted_price_usd * config.USD_TO_RUB_RATE, 2)
            price_ars = round(discounted_price_usd * config.USD_TO_ARS_RATE, 2)

            # Escaping dynamic parts for MarkdownV2
            esc_chosen_course_name = escape_markdown_v2(chosen_course_name)
            esc_booking_id = escape_markdown_v2(str(booking_id))
            esc_booking_duration_notice = escape_markdown_v2(BOOKING_DURATION_NOTICE)

            esc_tbank_card_number = escape_markdown_v2(config.TBANK_CARD_NUMBER)
            esc_tbank_card_holder = escape_markdown_v2(config.TBANK_CARD_HOLDER)
            esc_price_rub = escape_markdown_v2(f"{price_rub:.2f} RUB")

            esc_kaspi_card_number = escape_markdown_v2(config.KASPI_CARD_NUMBER)
            esc_price_kzt = escape_markdown_v2(f"{price_kzt:.2f} KZT")

            esc_ars_alias = escape_markdown_v2(config.ARS_ALIAS)
            esc_price_ars = escape_markdown_v2(f"{price_ars:.2f} ARS")
            
            esc_usdt_address = escape_markdown_v2(config.USDT_TRC20_ADDRESS)
            esc_price_usdt = escape_markdown_v2(f"{discounted_price_usd:.2f} USDT") 
            esc_crypto_network = escape_markdown_v2(config.CRYPTO_NETWORK)
            esc_binance_id = escape_markdown_v2(config.BINANCE_ID)

            # Add discount info to message if applicable
            discount_info = ""
            if discount_percent > 0:
                esc_discount_percent = escape_markdown_v2(str(discount_percent))
                esc_original_price = escape_markdown_v2(f"{course_price_usd_val:.2f}")
                esc_discounted_price = escape_markdown_v2(f"{discounted_price_usd:.2f}")
                discount_info = (
                    f"🎉 *Применена скидка {esc_discount_percent}%\!*\n"
                    f"Исходная цена: ~${esc_original_price}~\n"
                    f"Цена со скидкой: *${esc_discounted_price}*\n\n"
                )

            message_text = (
                f"📝 Ваше место на курс '*{esc_chosen_course_name}*' предварительно забронировано \(Заявка №*{esc_booking_id}*\)\.\n\n" 
                f"{discount_info}"
                f"⏳ _{esc_booking_duration_notice}_\n\n" 
                f"💳 *Реквизиты для оплаты:*\n\n" 
                f"*🇷🇺 Т\-Банк \(RUB\):*\n" 
                f"Карта: `{esc_tbank_card_number}`\n" 
                f"Получатель: {esc_tbank_card_holder}\n" 
                f"Сумма: `{esc_price_rub}`\n\n" 
                f"*🇰🇿 Kaspi \(KZT\):*\n" 
                f"Карта: `{esc_kaspi_card_number}`\n" 
                f"Сумма: `{esc_price_kzt}`\n\n" 
                f"*🇦🇷 Аргентинское Песо \(ARS\):*\n" 
                f"Alias: `{esc_ars_alias}`\n" 
                f"Сумма: `{esc_price_ars}`\n\n" 
                f"*💸 Криптовалюта \(USDT TRC\-20\):*\n"
                f"Адрес: `{esc_usdt_address}`\n" 
                f"Сеть: {esc_crypto_network}\n" 
                f"Сумма: `{esc_price_usdt}`\n" 
                f"Вы также можете оплатить по Binance ID: `{esc_binance_id}`\n\n" 
                f"_Пожалуйста, будьте внимательны при выборе сети для перевода USDT\._\n\n" 
                f"🧾 После оплаты, пожалуйста, отправьте фото чека прямо в этот чат\."
            )

            keyboard_payment = [
                [InlineKeyboardButton("❌ Отменить бронь", callback_data=f"{CALLBACK_CANCEL_RESERVATION}_{booking_id}")]
            ]
            reply_markup_payment = InlineKeyboardMarkup(keyboard_payment)

            await query.edit_message_text(text=message_text, reply_markup=reply_markup_payment, parse_mode=ParseMode.MARKDOWN_V2)

            # Don't clear pending_course_choice, pending_course_id, pending_course_price_usd here.
            # They are needed if the user cancels immediately after this message.
            # They will be cleared upon successful payment confirmation by admin or by explicit cancellation.
        except sqlite3.IntegrityError:
             logger.warning(f"User {current_user_id} might have tried to book the same course again too quickly.")
             await query.edit_message_text(text="Вы уже подали заявку на этот курс. Ожидайте информации или свяжитесь с нами.", reply_markup=None)
        except sqlite3.Error as e_db:
            logger.error(f"Database error for user {current_user_id}: {e_db}", exc_info=True)
            await query.edit_message_text(text="⚠️ Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.")
        except Exception as e_gen:
            logger.error(f"Unexpected error for user {current_user_id}: {e_gen}", exc_info=True)
            await query.edit_message_text(text="⚠️ Произошла непредвиденная ошибка.")
        finally:
            if conn:
                conn.close()

    elif query.data.startswith(CALLBACK_CANCEL_RESERVATION):
        parts = query.data.split('_')
        try:
            booking_id_to_cancel = int(parts[-1])
        except (IndexError, ValueError):
            logger.error(f"Invalid cancel reservation callback data: {query.data}")
            await query.edit_message_text("Ошибка: Некорректные данные для отмены.")
            return

        current_user_id = context.user_data.get('user_id', user_id)
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Update booking status to cancelled (e.g., confirmed = -1)
            # We only cancel if it's in state 0 (pending payment)
            cursor.execute(
                "UPDATE bookings SET confirmed = -1 WHERE id = ? AND user_id = ? AND confirmed = 0", 
                (booking_id_to_cancel, current_user_id)
            )
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"User {current_user_id} cancelled booking ID {booking_id_to_cancel}.")
                
                # Clean up user_data related to this booking
                if context.user_data.get(f'booking_id_{current_user_id}') == booking_id_to_cancel:
                    del context.user_data[f'booking_id_{current_user_id}']
                if 'pending_course_choice' in context.user_data:
                    del context.user_data['pending_course_choice']
                if 'pending_course_id' in context.user_data:
                    del context.user_data['pending_course_id']
                if 'pending_course_price_usd' in context.user_data:
                    del context.user_data['pending_course_price_usd']
                if 'pending_referral_code' in context.user_data:
                    del context.user_data['pending_referral_code']
                if 'pending_referral_info' in context.user_data:
                    del context.user_data['pending_referral_info']

                message_text = "Ваше предварительное бронирование отменено."
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Выбрать другой курс", callback_data=CALLBACK_BACK_TO_COURSE_SELECTION)]])
                await query.edit_message_text(text=message_text, reply_markup=reply_markup)
            else:
                logger.warning(f"User {current_user_id} tried to cancel booking ID {booking_id_to_cancel}, but it was not found or not in a cancellable state (confirmed=0).")
                await query.edit_message_text(text="Не удалось отменить бронирование. Возможно, оно уже обработано или отменено.")
        
        except sqlite3.Error as e_db:
            logger.error(f"DB error during cancellation for booking {booking_id_to_cancel}: {e_db}", exc_info=True)
            await query.edit_message_text("Ошибка базы данных при отмене бронирования.")
        except Exception as e:
            logger.error(f"Error during cancellation for booking {booking_id_to_cancel}: {e}", exc_info=True)
            await query.edit_message_text("Произошла ошибка при отмене бронирования.")
        finally:
            if conn:
                conn.close()

    elif query.data.startswith(CALLBACK_ADMIN_APPROVE_PAYMENT):
        parts = query.data.split('_')
        try:
            target_user_id = int(parts[-2])
            booking_id_to_approve = int(parts[-1])
        except (IndexError, ValueError):
            logger.error(f"Invalid admin approval callback data: {query.data}")
            await query.edit_message_text("Ошибка: Некорректные данные для подтверждения.")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE bookings SET confirmed = 2 WHERE id = ? AND user_id = ? AND confirmed = 1",
                (booking_id_to_approve, target_user_id)
            )
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Admin {user_id} approved payment for booking ID {booking_id_to_approve}, user {target_user_id}.")
                
                esc_booking_id_approved = escape_markdown_v2(str(booking_id_to_approve))
                esc_target_user_id = escape_markdown_v2(str(target_user_id))

                await query.edit_message_text(
                    f"✅ Оплата для заявки №*{esc_booking_id_approved}* \(Пользователь *{esc_target_user_id}*\) ПОДТВЕРЖДЕНА\.",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                # Get course details to check if it's a consultation
                cursor.execute(
                    "SELECT chosen_course, course_id FROM bookings WHERE id = ?",
                    (booking_id_to_approve,)
                )
                booking_details = cursor.fetchone()
                
                if booking_details:
                    chosen_course = booking_details[0]
                    course_id = booking_details[1]
                    
                    # Check if this is a consultation (ids 3 and 4 are consultations)
                    is_consultation = course_id in ["3", "4"]
                    
                    if is_consultation:
                        # For consultations, send message with calendar link
                        esc_calendar_link = escape_markdown_v2(CALENDAR_LINK)
                        esc_chosen_course = escape_markdown_v2(chosen_course)
                        
                        await context.bot.send_message(
                            chat_id=target_user_id,
                            text=f"🎉 Поздравляем\! Ваша оплата за консультацию *{esc_chosen_course}* \(заявка №*{esc_booking_id_approved}*\) подтверждена\!\n\n"
                                 f"Пожалуйста, выберите удобное для вас время для проведения консультации по ссылке:\n"
                                 f"{esc_calendar_link}",
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                    else:
                        # For regular courses, send standard confirmation
                        await context.bot.send_message(
                            chat_id=target_user_id,
                            text=f"🎉 Поздравляем\! Ваша оплата по заявке №*{esc_booking_id_approved}* подтверждена\. Место забронировано\!",
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                else:
                    # Fallback if booking details not found
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"🎉 Поздравляем\! Ваша оплата по заявке №*{esc_booking_id_approved}* подтверждена\.",
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
            else:
                logger.warning(f"Admin {user_id} tried to approve booking ID {booking_id_to_approve} for user {target_user_id}, but no matching pending record found or already processed.")
                await query.edit_message_text(f"⚠️ Заявка №{booking_id_to_approve} (Пользователь {target_user_id}) не найдена для подтверждения или уже обработана.")
        except sqlite3.Error as e_db:
            logger.error(f"DB error during admin approval: {e_db}", exc_info=True)
            await query.edit_message_text("Ошибка базы данных при подтверждении.")
        except Exception as e:
            logger.error(f"Error during admin approval: {e}", exc_info=True)
            await query.edit_message_text("Произошла ошибка при подтверждении.")
        finally:
            if conn:
                conn.close()
    else:
        logger.warning(f"Received unknown callback_data: {query.data} from user {user_id} ({first_name})")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return

    user = update.message.from_user
    user_id = user.id
    first_name = user.first_name or "Пользователь"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, chosen_course FROM bookings WHERE user_id = ? AND confirmed = 0 ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        booking_record = cursor.fetchone()

        if booking_record:
            booking_id = booking_record['id']
            chosen_course = booking_record['chosen_course']
            
            cursor.execute("UPDATE bookings SET confirmed = 1 WHERE id = ?", (booking_id,))
            conn.commit()
            logger.info(f"Photo received for booking ID {booking_id} from user {user_id}. Status updated to 1.")

            esc_first_name = escape_markdown_v2(first_name)
            esc_booking_id = escape_markdown_v2(str(booking_id))
            esc_chosen_course = escape_markdown_v2(chosen_course)
            esc_admin_contact = escape_markdown_v2(config.ADMIN_CONTACT)


            await update.message.reply_text(
                f"🙏 Спасибо, {esc_first_name}\! Ваше фото для заявки №*{esc_booking_id}* \(курс '*{esc_chosen_course}*' \) получено\.\n"
                f"Оплата проверяется\. Мы сообщим вам о результате\.\n"
                f"Если возникнут вопросы, свяжитесь с {esc_admin_contact}\.",
                parse_mode=ParseMode.MARKDOWN_V2
            )

            if config.TARGET_CHAT_ID == 0: 
                 logger.error("TARGET_CHAT_ID is not set. Cannot forward photo to admin chat.")
                 await update.message.reply_text("Не удалось уведомить администратора. Пожалуйста, свяжитесь с поддержкой.")
                 return
            
            esc_user_username = escape_markdown_v2(user.username or 'N/A')

            caption_for_admin = (
                f"🧾 *Новый чек для проверки\!*\n"
                f"Пользователь: {esc_first_name} \(ID: `{user_id}`\, @{esc_user_username}\)\n"
                f"Заявка №: *{esc_booking_id}*\n"
                f"Курс: *{esc_chosen_course}*"
            )
            
            forwarded_message = await context.bot.forward_message(
                chat_id=config.TARGET_CHAT_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            
            admin_keyboard = [
                [InlineKeyboardButton(f"✅ Одобрить (Заявка {booking_id})", callback_data=f"{CALLBACK_ADMIN_APPROVE_PAYMENT}{user_id}_{booking_id}")],
            ]
            admin_reply_markup = InlineKeyboardMarkup(admin_keyboard)
            await context.bot.send_message(
                chat_id=config.TARGET_CHAT_ID,
                text=caption_for_admin, 
                reply_markup=admin_reply_markup,
                reply_to_message_id=forwarded_message.message_id if forwarded_message else None,
                parse_mode=ParseMode.MARKDOWN_V2
            )

        else:
            logger.info(f"Photo received from user {user_id}, but no active booking (status 0) found.")
            await update.message.reply_text(
                "Спасибо за фото! Не могу найти активную заявку для вас. Если вы недавно выбирали курс, попробуйте еще раз или свяжитесь с поддержкой."
            )

    except sqlite3.Error as e_db:
        logger.error(f"DB error in photo_handler for user {user_id}: {e_db}", exc_info=True)
        await update.message.reply_text("Произошла ошибка при обработке вашего фото. Пожалуйста, попробуйте позже.")
    except Exception as e:
        logger.error(f"Error in photo_handler for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text("Произошла непредвиденная ошибка при обработке фото.")
    finally:
        if conn:
            conn.close()


async def create_referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new referral coupon"""
    user = update.message.from_user
    user_id = user.id
    
    # Check if user is admin
    if referral_config.REFERRAL_ADMIN_IDS and user_id not in referral_config.REFERRAL_ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для создания реферальных купонов.")
        return
    
    # Parse command arguments
    if not context.args or len(context.args) < 2:
        available_discounts = ", ".join([f"{k}%" for k in referral_config.REFERRAL_DISCOUNTS.keys()])
        await update.message.reply_text(
            f"Использование: /create_referral <процент_скидки> <количество_активаций>\n\n"
            f"Доступные скидки: {available_discounts}\n"
            f"Пример: /create_referral 10 50"
        )
        return
    
    try:
        discount_percent = int(context.args[0])
        max_activations = int(context.args[1])
        
        if discount_percent not in referral_config.REFERRAL_DISCOUNTS:
            available_discounts = ", ".join([f"{k}%" for k in referral_config.REFERRAL_DISCOUNTS.keys()])
            await update.message.reply_text(f"❌ Недопустимый процент скидки. Доступные: {available_discounts}")
            return
        
        if max_activations <= 0:
            await update.message.reply_text("❌ Количество активаций должно быть больше 0.")
            return
        
        # Generate unique referral code
        code = generate_referral_code()
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""INSERT INTO {referral_config.REFERRAL_TABLE_NAME} 
            (code, discount_percent, max_activations, created_by) 
            VALUES (?, ?, ?, ?)""",
            (code, discount_percent, max_activations, user_id)
        )
        conn.commit()
        conn.close()
        
        # Get bot username for link generation
        bot_username = context.bot.username
        referral_link = f"https://t.me/{bot_username}?start={referral_config.REFERRAL_START_PARAMETER}{code}"
        
        escaped_link = escape_markdown_v2(referral_link)
        escaped_code = escape_markdown_v2(code)
        
        await update.message.reply_text(
            f"✅ Реферальный купон создан\!\n\n"
            f"📎 Код: `{escaped_code}`\n"
            f"💸 Скидка: {discount_percent}%\n"
            f"🔢 Количество активаций: {max_activations}\n\n"
            f"🔗 Реферальная ссылка:\n`{escaped_link}`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
    except ValueError:
        await update.message.reply_text("❌ Неверный формат команды. Используйте числа для процента и количества.")
    except Exception as e:
        logger.error(f"Error in create_referral_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка при создании купона.")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить текущую сессию и начать заново"""
    # Очищаем все данные пользователя
    context.user_data.clear()
    
    await update.message.reply_text(
        "🔄 Ваша сессия сброшена. Вы можете начать заново.\n\n"
        "Используйте /start для начала работы."
    )

async def referral_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral statistics"""
    user = update.message.from_user
    user_id = user.id
    
    # Check if user is admin
    if referral_config.REFERRAL_ADMIN_IDS and user_id not in referral_config.REFERRAL_ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для просмотра статистики купонов.")
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all coupons statistics
        cursor.execute(f"""
            SELECT code, discount_percent, max_activations, current_activations, 
                   created_at, is_active
            FROM {referral_config.REFERRAL_TABLE_NAME}
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        coupons = cursor.fetchall()
        
        if not coupons:
            await update.message.reply_text("📊 Нет созданных реферальных купонов.")
            return
        
        message = "📊 *Статистика реферальных купонов:*\n\n"
        
        for coupon in coupons:
            code = coupon['code']
            discount = coupon['discount_percent']
            max_uses = coupon['max_activations']
            current_uses = coupon['current_activations']
            is_active = coupon['is_active']
            created_at = coupon['created_at']
            
            status = "✅ Активен" if is_active and current_uses < max_uses else "❌ Неактивен"
            
            esc_code = escape_markdown_v2(code)
            esc_status = escape_markdown_v2(status)
            
            message += (
                f"📎 Код: `{esc_code}`\n"
                f"💸 Скидка: {discount}%\n"
                f"🔢 Использований: {current_uses}/{max_uses}\n"
                f"📅 Статус: {esc_status}\n"
                f"➖➖➖➖➖➖➖➖➖\n"
            )
        
        conn.close()
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
        
    except Exception as e:
        logger.error(f"Error in referral_stats_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка при получении статистики.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    if isinstance(context.error, Conflict):
        logger.critical(
            "TELEGRAM CONFLICT ERROR DETECTED. "
            "This means another instance of the bot is running with the same token. "
            "Please ensure only ONE instance is active."
        )

async def post_initialization(application: Application) -> None:
    logger.info("Running post-initialization: Attempting to delete webhook...")
    bot_token = application.bot.token
    if not bot_token:
        logger.error("Bot token not found in application object.")
        return

    webhook_delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=true"
    try:
        with urllib.request.urlopen(webhook_delete_url, timeout=10) as response:
            response_body = response.read().decode()
            logger.info(f"Webhook deletion API response: {response_body}")
            if '"ok":true' not in response_body.lower():
                logger.warning("Webhook deletion might not have been successful.")
    except urllib.error.URLError as e:
        logger.error(f"URLError while trying to delete webhook: {e.reason}")
    except Exception as e:
        logger.error(f"Unexpected error during webhook deletion: {e}", exc_info=True)
    await asyncio.sleep(2)

def main() -> None:
    logger.info("Starting bot application setup...")
    persistence = PicklePersistence(filepath=config.PERSISTENCE_FILEPATH)
    application = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .post_init(post_initialization)
        .persistence(persistence)
        .build()
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("create_referral", create_referral_command))
    application.add_handler(CommandHandler("referral_stats", referral_stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, photo_handler))
    application.add_error_handler(error_handler)
    
    logger.info("Bot starting to poll for updates...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    logger.info("Bot application has stopped.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Critical error during bot startup: {e}", exc_info=True)
        sys.exit(1)
