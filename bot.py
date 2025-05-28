import sqlite3
import logging
import sys
from datetime import datetime
import asyncio
import urllib.request
import urllib.error
import config
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
        "price_usd": 70,
        "description": "На этом курсе в течение двух недель я учу превращать идеи в рабочие прототипы. Программируем на русском языке. Наглядно объясняю как работает ИИ, интернет и приложения. Общение в закрытой группе, домашки, три созвона с записями. Поддержка продолжается месяц после курса.\nПосле обучения ты будешь знать как создавать сайты с помощью ИИ, что такое база данных, как собрать телеграм бота за вечер и выложить проект в интернет. Набор промптов в подарок!\nДля кого: вообще для всех\nДлительность: две недели\nФормат: 2 двухчасовых созвона по средам в 20:00 МСК\nСтоимость: 70$\nСтарт: 28 мая\n\nОплата возможна переводом на карты Т-Банка, Каспи или в USDT на крипто кошелек.\n\nЧто дальше: После оплаты я добавлю тебя в закрытую группу, где мы будем общаться и делиться материалами. Перед стартом курса пришлю всю необходимую информацию."
    },
    {
        "id": "3",
        "button_text": "Блокчейн консультация",
        "name": "Блокчейн (разовая консультация)",
        "price_usd": 25,
        "description": "Как завести крипто кошелек, пополнить его, спустить на мемкоины через децентрализованные биржи, сделать мемкоин про своего кота, а потом обналичить миллион.\nДля кого: для энтузиастов новой цифровой экономики\nФормат: полуторачасовое онлайн занятие в удобное для тебя время\nСтоимость: 25$\n\nОплата возможна переводом на карты Т-Банка, Каспи или в USDT на крипто кошелек."
    },
    {
        "id": "4",
        "button_text": "ChatGPT консультация",
        "name": "ChatGPT (разовая консультация)",
        "price_usd": 25,
        "description": "Как использовать величайшее изобретение человечества на сто процентов.\nДля кого: для всех\nФормат: полуторачасовое онлайн занятие в удобное для тебя время\nСтоимость: 25$\n\nОплата возможна переводом на карты Т-Банка, Каспи или в USDT на крипто кошелек."
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
                UNIQUE(user_id, chosen_course, created_at)
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database table creation/check error: {e}")
    return conn

def get_course_selection_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    for course in COURSES:
        keyboard.append([InlineKeyboardButton(course["button_text"], callback_data=f"{CALLBACK_SELECT_COURSE_PREFIX}{course['id']}")])
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Посмотреть доступные курсы", callback_data=CALLBACK_RESERVE_SPOT)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        if update.message:
            await update.message.reply_text(
                "Привет! Добро пожаловать в школу HashSlash! 👋\n\n"
                "Меня зовут Сережа, и последние 10 лет я помогаю людям осваивать современные инструменты и технологии.\n\n"
                "Сейчас я открыл набор в группу по вайбкодингу. Вайбкодинг – это новый способ создавать приложения и сайты, не тратя годы на изучение программирования.\n\n"
                "Представьте: вы просто рассказываете искусственному интеллекту (ИИ) на обычном языке, каким должно быть ваше приложение или сайт, а он сам создаёт всё за вас.\n\n"
                "Вы – как режиссёр, который задаёт идею и направление. Вам не нужно разбираться в коде или технических деталях – вы сосредотачиваетесь на том, что делает ваш продукт крутым: его дизайн, удобство и ценность для пользователей.\n\n"
                "Вайбкодинг открывает разработку для всех, кто хочет воплотить свои идеи, даже без технических навыков.",
                reply_markup=reply_markup
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

    if query.data == CALLBACK_RESERVE_SPOT or query.data == CALLBACK_BACK_TO_COURSE_SELECTION:
        reply_markup = get_course_selection_keyboard()
        message_text = "Свободная касса! Сезон 2025 лето, открыты курсы для записи.\n\nЯ провожу групповые курсы и индивидуальные консультации по различным темам. Сейчас я набираю группу на курс по вайбкодингу, а также доступны индивидуальные консультации по другим направлениям. Выберите интересующий вас вариант:"
        try:
            await query.edit_message_text(text=message_text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error editing message for {query.data}: {e}", exc_info=True)

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

        message_text = (
            f"Вы выбрали курс: *{escaped_course_name}*\n"
            f"Имя: *{escaped_first_name}*\n\n"
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
            cursor.execute(
                """INSERT INTO bookings (user_id, username, first_name, chosen_course, course_id, confirmed)
                   VALUES (?, ?, ?, ?, ?, 0)""",
                (current_user_id, current_username, current_first_name, chosen_course_name, course_id)
            )
            booking_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Preliminary booking ID {booking_id} for user {current_user_id} ({current_first_name}), course '{chosen_course_name}' saved (status 0).")

            context.user_data[f'booking_id_{current_user_id}'] = booking_id

            # Calculate payment amounts
            price_kzt = round(course_price_usd_val * config.USD_TO_KZT_RATE, 2)
            price_rub = round(course_price_usd_val * config.USD_TO_RUB_RATE, 2)
            price_ars = round(course_price_usd_val * config.USD_TO_ARS_RATE, 2)

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
            esc_price_usdt = escape_markdown_v2(f"{course_price_usd_val:.2f} USDT") 
            esc_crypto_network = escape_markdown_v2(config.CRYPTO_NETWORK)
            esc_binance_id = escape_markdown_v2(config.BINANCE_ID)

            message_text = (
                f"📝 Ваше место на курс '*{esc_chosen_course_name}*' предварительно забронировано \(Заявка №*{esc_booking_id}*\)\.\n\n" 
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
