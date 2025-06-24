import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import constants
import database
from utils import escape_markdown_v2

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command, including referral code logic."""
    user = update.message.from_user
    logger.info(f"START command from user {user.id} ({user.first_name})")

    if context.args and len(context.args) > 0:
        start_param = context.args[0]
        if start_param.startswith(constants.REFERRAL_START_PARAMETER):
            referral_code = start_param[len(constants.REFERRAL_START_PARAMETER):]
            coupon, status = database.validate_referral_code(referral_code, user.id)

            logger.info(f"Referral attempt by user {user.id} with code {referral_code}. Status: {status}")

            if status == "valid":
                context.user_data['pending_referral_code'] = referral_code
                context.user_data['pending_referral_info'] = dict(coupon)

                remaining = coupon['max_activations'] - coupon['current_activations']
                discount_msg = constants.REFERRAL_APPLIED_MESSAGE.format(discount=coupon['discount_percent'])
                if coupon['name']:
                    discount_msg += f"\n🏷️ Купон: {coupon['name']}"
                discount_msg += f"\n📊 Осталось активаций: {remaining}"
                await update.message.reply_text(discount_msg)
            else:
                await update.message.reply_text(constants.REFERRAL_EXPIRED_MESSAGE)

    keyboard = [[InlineKeyboardButton("Посмотреть программу", callback_data=constants.CALLBACK_RESERVE_SPOT)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Добро пожаловать в школу HashSlash! 👋\n\n"
        "Меня зовут Сережа, я основатель креативной студии <a href='https://hsl.sh/'>хсл щ</a>. Последние 10 лет я помогаю людям осваивать современные инструменты и технологии.\n\n"
        "Сейчас я открыл набор в группу по <b>вайбкодингу</b>. Вайбкодинг — это новый способ создавать приложения и сайты, не тратя годы на изучение программирования.",
        reply_markup=reply_markup,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clears all user data for the current chat session."""
    context.user_data.clear()
    logger.info(f"User {update.message.from_user.id} reset their session.")
    await update.message.reply_text(
        "🔄 Ваша сессия сброшена. Вы можете начать заново, используя /start."
    )

async def create_referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to create a new referral coupon."""
    user = update.message.from_user
    if constants.REFERRAL_ADMIN_IDS and user.id not in constants.REFERRAL_ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для создания реферальных купонов.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Использование: /create_referral <процент> <активации>")
        return

    try:
        discount = int(context.args[0])
        activations = int(context.args[1])

        if discount not in constants.REFERRAL_DISCOUNTS:
            await update.message.reply_text("❌ Недопустимый процент скидки.")
            return

        code = database.generate_and_save_referral_code(discount, activations, user.id)
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start={constants.REFERRAL_START_PARAMETER}{code}"

        logger.info(f"Admin {user.id} created a new referral code: {code}")
        await update.message.reply_text(
            f"✅ Купон создан\!\nКод: `{escape_markdown_v2(code)}`\n"
            f"Скидка: {discount}%\nАктиваций: {activations}\n\n"
            f"Ссылка: `{escape_markdown_v2(link)}`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Неверный формат. Пример: /create_referral 20 10")
    except Exception as e:
        logger.error(f"Error creating referral code: {e}")
        await update.message.reply_text("❌ Произошла ошибка при создании купона.")

async def referral_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to view referral coupon statistics."""
    user = update.message.from_user
    if constants.REFERRAL_ADMIN_IDS and user.id not in constants.REFERRAL_ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для просмотра статистики.")
        return

    coupons = database.get_referral_stats()
    if not coupons:
        await update.message.reply_text("📊 Нет созданных реферальных купонов.")
        return

    message = "📊 *Статистика реферальных купонов:*\n\n"
    for coupon in coupons:
        status = "✅" if coupon['is_active'] and coupon['current_activations'] < coupon['max_activations'] else "❌"
        message += (
            f"{status} Код: `{escape_markdown_v2(coupon['code'])}`\n"
            f"   Скидка: {coupon['discount_percent']}%, "
            f"Исп\.: {coupon['current_activations']}/{coupon['max_activations']}\n"
            f"-------------------\n"
        )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)