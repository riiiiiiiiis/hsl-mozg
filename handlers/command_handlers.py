import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import constants
from utils import escape_markdown_v2
from db import courses as db_courses
from db import events as db_events
from db import referrals as db_referrals

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command, dynamically loading courses."""
    user = update.message.from_user
    db_events.log_event(
        user.id, 
        'start_command',
        username=user.username,
        first_name=user.first_name
    )
    logger.info(f"START command from user {user.id} ({user.first_name})")

    if context.args and len(context.args) > 0:
        start_param = context.args[0]
        if start_param.startswith(constants.REFERRAL_START_PARAMETER):
            referral_code = start_param[len(constants.REFERRAL_START_PARAMETER):]
            coupon, status = db_referrals.validate_referral_code(referral_code, user.id)

            logger.info(f"Referral attempt by user {user.id} with code {referral_code}. Status: {status}")
            if status == "valid":
                context.user_data['pending_referral_code'] = referral_code
                context.user_data['pending_referral_info'] = dict(coupon)
                
                # Логируем использование реферального кода
                db_events.log_event(
                    user.id, 
                    'referral_code_used',
                    details={'referral_code': referral_code, 'discount': coupon['discount_percent']},
                    username=user.username,
                    first_name=user.first_name
                )
                
                remaining = coupon['max_activations'] - coupon['current_activations']
                discount_msg = constants.REFERRAL_APPLIED_MESSAGE.format(discount=coupon['discount_percent'])
                if coupon['name']:
                    discount_msg += f"\n🏷️ Купон: {coupon['name']}"
                discount_msg += f"\n📊 Осталось активаций: {remaining}"
                
                await update.message.reply_text(discount_msg)
            else:
                await update.message.reply_text(constants.REFERRAL_EXPIRED_MESSAGE)

    active_courses = db_courses.get_active_courses()
    
    keyboard = []
    if active_courses:
        for course in active_courses:
            callback_data = f"{constants.CALLBACK_SELECT_COURSE_PREFIX}{course['id']}"
            keyboard.append([InlineKeyboardButton(course['button_text'], callback_data=callback_data)])
        
        message_text = "Привет! Добро пожаловать в школу HashSlash! 👋\n\n" \
                       "Выберите интересующий вас курс из списка ниже:"
    else:
        message_text = "К сожалению, сейчас нет доступных курсов. Загляните попозже!"

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clears all user data for the current chat session."""
    user = update.message.from_user
    # Логируем сброс сессии
    db_events.log_event(
        user.id, 
        'session_reset',
        username=user.username,
        first_name=user.first_name
    )
    context.user_data.clear()
    logger.info(f"User {user.id} reset their session.")
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

        code = db_referrals.generate_and_save_referral_code(discount, activations, user.id)
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start={constants.REFERRAL_START_PARAMETER}{code}"

        # Логируем создание реферального кода
        db_events.log_event(
            user.id, 
            'referral_created',
            details={'code': code, 'discount': discount, 'activations': activations},
            username=user.username,
            first_name=user.first_name
        )
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
    # Логируем запрос статистики
    db_events.log_event(
        user.id, 
        'referral_stats_requested',
        username=user.username,
        first_name=user.first_name
    )
    if constants.REFERRAL_ADMIN_IDS and user.id not in constants.REFERRAL_ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для просмотра статистики.")
        return

    coupons = db_referrals.get_referral_stats()
    if not coupons:
        await update.message.reply_text("📊 Нет созданных реферальных купонов.")
        return

    message = "📊 *Статистика реферальных купонов:*\n\n"
    for coupon in coupons:
        status = "✅ Активен" if coupon['is_active'] and coupon['current_activations'] < coupon['max_activations'] else "❌ Неактивен"
        message += (
            f"{status} Код: `{escape_markdown_v2(coupon['code'])}`\n"
            f"   Скидка: {coupon['discount_percent']}%, "
            f"Исп\.: {coupon['current_activations']}/{coupon['max_activations']}\n"
            f"-------------------\n"
        )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get a quick statistics summary."""
    user = update.message.from_user
    # Логируем запрос статистики
    db_events.log_event(
        user.id, 
        'stats_requested',
        username=user.username,
        first_name=user.first_name
    )
    try:
        stats = db_events.get_stats_summary()
        message = (
            f"📊 *Статистика*\n\n"
            f"👤 *Пользователи:*\n"
            f"  - Сегодня: *{stats['users_today']}*\n"
            f"  - За 7 дней: *{stats['users_week']}*\n\n"
            f"💰 *Продажи:*\n"
            f"  - Новых броней сегодня: *{stats['bookings_today']}*\n"
            f"  - Оплат за 7 дней: *{stats['confirmed_week']}*"
        )
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await update.message.reply_text("Не удалось получить статистику.")