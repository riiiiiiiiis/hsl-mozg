import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
from handlers.callbacks import *
from locales.ru import get_text
# Removed escape_markdown_v2 import - using HTML now
from utils.lessons import get_active_lessons
from utils.courses import get_active_courses
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
        if start_param.startswith(config.REFERRAL_START_PARAMETER):
            referral_code = start_param[len(config.REFERRAL_START_PARAMETER):]
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
                discount_msg = get_text("REFERRAL", "APPLIED").format(discount=coupon['discount_percent'])
                if coupon['name']:
                    discount_msg += f"\n🏷️ Купон: {coupon['name']}"
                discount_msg += f"\n📊 Осталось активаций: {remaining}"
                
                await update.message.reply_text(discount_msg)
            else:
                await update.message.reply_text(get_text("REFERRAL", "EXPIRED"))

    active_courses = get_active_courses()
    
    keyboard = []
    
    # Добавляем кнопки бесплатных уроков, если они активны
    active_lessons = get_active_lessons()
    for lesson_type, lesson_data in active_lessons.items():
        callback_data = f"{CALLBACK_FREE_LESSON_PREFIX}{lesson_data['id']}"
        keyboard.append([InlineKeyboardButton(
            lesson_data['button_text'], 
            callback_data=callback_data
        )])
    
    # Добавляем кнопки курсов
    if active_courses:
        for course in active_courses:
            callback_data = f"{CALLBACK_SELECT_COURSE_PREFIX}{course['id']}"
            keyboard.append([InlineKeyboardButton(course['button_text'], callback_data=callback_data)])
        message_text = get_text("START", "WELCOME_WITH_COURSES")
    else:
        message_text = get_text("START", "WELCOME_NO_COURSES")

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
    await update.message.reply_text(get_text("RESET", "SESSION_CLEARED"))

async def create_referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to create a new referral coupon."""
    user = update.message.from_user
    if config.REFERRAL_ADMIN_IDS and user.id not in config.REFERRAL_ADMIN_IDS:
        await update.message.reply_text(get_text("REFERRAL_ADMIN", "NO_RIGHTS"))
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(get_text("REFERRAL_ADMIN", "USAGE_HINT"))
        return

    try:
        discount = int(context.args[0])
        activations = int(context.args[1])

        if discount not in config.REFERRAL_DISCOUNTS:
            await update.message.reply_text(get_text("REFERRAL_ADMIN", "INVALID_FORMAT"))
            return

        code = db_referrals.generate_and_save_referral_code(discount, activations, user.id)
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start={config.REFERRAL_START_PARAMETER}{code}"

        # Логируем создание реферального кода
        db_events.log_event(
            user.id, 
            'referral_created',
            details={'code': code, 'discount': discount, 'activations': activations},
            username=user.username,
            first_name=user.first_name
        )
        logger.info(f"Admin {user.id} created a new referral code: {code}")
        message_text = get_text(
            "REFERRAL_ADMIN",
            "CREATED_OK",
            code=code,
            discount=discount,
            activations=activations,
            link=link
        )
        await update.message.reply_text(message_text, parse_mode='HTML')
    except (ValueError, IndexError):
        await update.message.reply_text(get_text("REFERRAL_ADMIN", "INVALID_FORMAT"))
    except Exception as e:
        logger.error(f"Error creating referral code: {e}")
        await update.message.reply_text(get_text("REFERRAL_ADMIN", "ERROR_CREATING"))

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
    if config.REFERRAL_ADMIN_IDS and user.id not in config.REFERRAL_ADMIN_IDS:
        await update.message.reply_text(get_text("REFERRAL_STATS", "NO_RIGHTS"))
        return

    coupons = db_referrals.get_referral_stats()
    if not coupons:
        await update.message.reply_text(get_text("REFERRAL_STATS", "EMPTY"))
        return

    lines = []
    for coupon in coupons:
        status = "✅ Активен" if coupon['is_active'] and coupon['current_activations'] < coupon['max_activations'] else "❌ Неактивен"
        lines.append(
            f"{status} Код: <code>{coupon['code']}</code>\n"
            f"   Скидка: {coupon['discount_percent']}%, "
            f"Исп.: {coupon['current_activations']}/{coupon['max_activations']}\n"
            f"-------------------"
        )
    stats_block = "\n".join(lines) + "\n"
    message = get_text("REFERRAL_STATS", "TEMPLATE", stats_block=stats_block)
    await update.message.reply_text(message, parse_mode='HTML')

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
        message = get_text(
            "STATS",
            "TEMPLATE",
            users_today=stats['users_today'],
            users_week=stats['users_week'],
            bookings_today=stats['bookings_today'],
            confirmed_week=stats['confirmed_week']
        )
        await update.message.reply_text(message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await update.message.reply_text("Не удалось получить статистику.")