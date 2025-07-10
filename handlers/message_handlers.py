import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
import constants
from utils import escape_markdown_v2
from db import bookings as db_bookings
from db import events as db_events

logger = logging.getLogger(__name__)

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

    caption_for_admin = (
        f"🧾 *Новый чек для проверки\!*\n"
        f"Пользователь: {escape_markdown_v2(user.first_name)} \(ID: `{user.id}`\)\n"
        f"Заявка №: *{escape_markdown_v2(str(booking_id))}*\n"
        f"Курс: *{escape_markdown_v2(course_name)}*"
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