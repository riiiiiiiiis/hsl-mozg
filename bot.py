import sqlite3
import logging
import sys
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

BOOKING_DURATION_NOTICE = "Ваше место предварительно забронировано на 1 час. Пожалуйста, произведите оплату и отправьте фото чека в этот чат для подтверждения."


COURSE_NAME = "Вайб Кодинг"
COURSE_DATE_1 = "01.07.2025"
COURSE_DATE_2 = "15.07.2025"
COURSE_DESCRIPTION_TEST = "Это интенсивный курс, который поможет вам погрузиться в мир современного программирования, освоить ключевые технологии и создать свой первый проект. Мы сфокусируемся на практических навыках и актуальных инструментах."


COURSE_1_TEXT = f"{COURSE_NAME} ({COURSE_DATE_1})"
COURSE_2_TEXT = f"{COURSE_NAME} ({COURSE_DATE_2})"

CALLBACK_RESERVE_SPOT = "reserve_spot"
CALLBACK_SELECT_COURSE_1 = "select_course_1"
CALLBACK_SELECT_COURSE_2 = "select_course_2"
CALLBACK_CONFIRM_COURSE_SELECTION = "confirm_course_selection_v2"
CALLBACK_BACK_TO_COURSE_SELECTION = "back_to_course_selection"
CALLBACK_ADMIN_APPROVE_PAYMENT = "admin_approve_"
CALLBACK_ADMIN_REJECT_PAYMENT = "admin_reject_"

def escape_markdown_v2(text: str) -> str:
    """Helper function to escape text for MarkdownV2 parsing."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return "".join(f'\\{char}' if char in escape_chars else char for char in str(text))


def get_db_connection():
    conn = sqlite3.connect(config.DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                chosen_course TEXT,
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
    keyboard = [
        [InlineKeyboardButton(COURSE_1_TEXT, callback_data=CALLBACK_SELECT_COURSE_1)],
        [InlineKeyboardButton(COURSE_2_TEXT, callback_data=CALLBACK_SELECT_COURSE_2)],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Забронировать место", callback_data=CALLBACK_RESERVE_SPOT)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        if update.message:
            await update.message.reply_text(
                "Добро пожаловать! Нажмите кнопку ниже, чтобы забронировать место:",
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
        message_text = "Пожалуйста, выберите один из курсов:"
        try:
            await query.edit_message_text(text=message_text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error editing message for {query.data}: {e}", exc_info=True)

    elif query.data == CALLBACK_SELECT_COURSE_1 or query.data == CALLBACK_SELECT_COURSE_2:
        chosen_course_text = COURSE_1_TEXT if query.data == CALLBACK_SELECT_COURSE_1 else COURSE_2_TEXT
        context.user_data['pending_course_choice'] = chosen_course_text
        
        escaped_course_text = escape_markdown_v2(chosen_course_text)
        escaped_first_name = escape_markdown_v2(first_name)
        escaped_course_description = escape_markdown_v2(COURSE_DESCRIPTION_TEST)


        message_text = (
            f"Вы выбрали курс: *{escaped_course_text}*\n"
            f"Имя: *{escaped_first_name}*\n\n"
            f"*{escaped_course_description}*\n\n" # Test course description
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
        chosen_course = context.user_data.get('pending_course_choice')

        if not chosen_course:
            logger.warning(f"User {current_user_id} tried to confirm course, but 'pending_course_choice' not found.")
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
                """INSERT INTO bookings (user_id, username, first_name, chosen_course, confirmed)
                   VALUES (?, ?, ?, ?, 0)""",
                (current_user_id, current_username, current_first_name, chosen_course)
            )
            booking_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Preliminary booking ID {booking_id} for user {current_user_id} ({current_first_name}), course '{chosen_course}' saved (status 0).")

            context.user_data[f'booking_id_{current_user_id}'] = booking_id

            # Escaping dynamic parts for MarkdownV2
            esc_chosen_course = escape_markdown_v2(chosen_course)
            esc_booking_id = escape_markdown_v2(str(booking_id))
            esc_booking_duration_notice = escape_markdown_v2(BOOKING_DURATION_NOTICE)
            
            esc_card_details = escape_markdown_v2(config.CARD_PAYMENT_DETAILS)
            esc_card_amount = escape_markdown_v2(config.CARD_PAYMENT_AMOUNT)
            
            crypto_wallet_md = f"`{config.CRYPTO_WALLET_ADDRESS}`" # Backticks for inline code, no need to escape address itself here
            esc_crypto_amount = escape_markdown_v2(config.CRYPTO_PAYMENT_AMOUNT)
            esc_crypto_network = escape_markdown_v2(config.CRYPTO_NETWORK) # CRYPTO_NETWORK might contain '-'


            message_text = (
                f"📝 Ваше место на курс '*{esc_chosen_course}*' предварительно забронировано \(Заявка №*{esc_booking_id}*\)\.\n\n"
                f"⏳ _{esc_booking_duration_notice}_\n\n"
                f"💳 *Реквизиты для оплаты:*\n\n"
                f"*Карта:*\n"
                f"{esc_card_details}\n"
                f"Сумма: `{esc_card_amount}`\n\n"
                f"*Криптовалюта \(USDT TRC\\-20\):*\n" # Escaped hyphen in TRC-20
                f"Кошелек: {crypto_wallet_md}\n"
                f"Сумма: `{esc_crypto_amount}`\n"
                f"Сеть: {esc_crypto_network}\n\n" # esc_crypto_network will handle escaping for "TRC-20 (Tron)"
                f"_Пожалуйста, будьте внимательны при выборе сети для перевода USDT\._\n\n"
                f"🧾 После оплаты, пожалуйста, отправьте фото чека прямо в этот чат\."
            )

            await query.edit_message_text(text=message_text, reply_markup=None, parse_mode=ParseMode.MARKDOWN_V2)

            if 'pending_course_choice' in context.user_data:
                del context.user_data['pending_course_choice']
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
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"🎉 Поздравляем\! Ваша оплата по заявке №*{esc_booking_id_approved}* подтверждена\. Место забронировано\!",
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
