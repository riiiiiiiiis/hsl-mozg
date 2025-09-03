"""
Локализация для русского языка
Все текстовые сообщения для пользователей
"""

# Сообщения для бесплатных уроков
FREE_LESSON = {
    "EMAIL_REQUEST": "📧 Для записи на бесплатный урок введите ваш email адрес:",
    "EMAIL_INVALID": "❌ Неверный формат email. Пожалуйста, введите корректный email адрес (например: example@mail.com)",
    "REGISTRATION_SUCCESS": "✅ Отлично! Вы записаны на бесплатный урок.\n\n📅 Дата: {date}\n📧 Email: {email}\n\n🔔 Ссылка на видеовстречу будет отправлена сюда за 15 минут перед началом урока.",
    "ALREADY_REGISTERED": "ℹ️ Вы уже зарегистрированы на бесплатный урок.\n\n📅 Дата: {date}\n🔔 Ссылка будет отправлена перед началом.",
    "REMINDER": "🎯 Бесплатный урок уже скоро!\n\n📅 {date}\n🔗 Ссылка: {link}\n\nУвидимся на уроке! 👋"
}

# Сообщения реферальной системы
REFERRAL = {
    "APPLIED": "🎉 Применен купон на {discount}% скидку!",
    "EXPIRED": "❌ К сожалению, этот купон больше не активен.",
    "ALREADY_USED": "❌ Вы уже использовали этот купон ранее."
}

# Общие сообщения
BOOKING = {
    "DURATION_NOTICE": "Ваше место предварительно забронировано на 1 час. Пожалуйста, произведите оплату и отправьте фото чека в этот чат для подтверждения.",
    "CALENDAR_LINK": "https://calendar.app.google/gYhZNcreyWrAuEgT9"
}

# Приветствие и старт
START = {
    "WELCOME_WITH_COURSES": (
        "Привет! 👋\n\n"
        "Здесь учимся превращать идеи в цифровые продукты — приложения, игры и сайты через диалог с нейросетями.\n\n"
        "Хочешь сначала попробовать? \n"
        "Приходи на бесплатный воркшоп 12 сентября, кнопка для записи ниже👇\n\n"
        "Сразу есть настрой на системное обучение? \n"
        "Выбирай курс: «Основы» (старт — 4 сентября)"
    ),
    "WELCOME_NO_COURSES": (
        "Привет! 👋\n\n"
        "Здесь учимся превращать идеи в цифровые продукты — приложения, игры и сайты через диалог с нейросетями.\n\n"
        "Хочешь сначала попробовать? \n"
        "Приходи на бесплатный воркшоп, кнопка для записи ниже👇"
    )
}

# Сброс сессии
RESET = {
    "SESSION_CLEARED": "🔄 Ваша сессия сброшена. Вы можете начать заново, используя /start."
}

# Админские команды для рефералов (HTML)
REFERRAL_ADMIN = {
    "NO_RIGHTS": "❌ У вас нет прав для выполнения этой команды.",
    "USAGE_HINT": "Использование: /create_referral <процент> <активации>",
    "INVALID_FORMAT": "❌ Неверный формат. Пример: /create_referral 20 10",
    "CREATED_OK": (
        "✅ Купон создан!\n"
        "Код: <code>{code}</code>\n"
        "Скидка: {discount}%\n"
        "Активаций: {activations}\n\n"
        "Ссылка: <code>{link}</code>"
    ),
    "ERROR_CREATING": "❌ Произошла ошибка при создании купона."
}

# Статистика реферальных купонов (HTML)
REFERRAL_STATS = {
    "NO_RIGHTS": "❌ У вас нет прав для просмотра статистики.",
    "EMPTY": "📊 Нет созданных реферальных купонов.",
    "TEMPLATE": "📊 <b>Статистика реферальных купонов:</b>\n\n{stats_block}"
}

# Сводная статистика (HTML)
STATS = {
    "TEMPLATE": (
        "📊 <b>Статистика</b>\n\n"
        "👤 <b>Пользователи:</b>\n"
        "  - Сегодня: <b>{users_today}</b>\n"
        "  - За 7 дней: <b>{users_week}</b>\n\n"
        "💰 <b>Продажи:</b>\n"
        "  - Новых броней сегодня: <b>{bookings_today}</b>\n"
        "  - Оплат за 7 дней: <b>{confirmed_week}</b>"
    )
}

# Поток бронирования / общий пользовательский флоу
BOOKING_FLOW = {
    "COURSE_UNAVAILABLE": "Извините, этот курс больше не доступен.",
    "SESSION_EXPIRED": "Произошла ошибка, сессия истекла. Пожалуйста, начните заново с /start.",
    "BOOKING_FAILED": "Не удалось создать бронирование. Пожалуйста, попробуйте снова.",
    "BOOKING_CANCELLED": "Ваше бронирование отменено. Вы можете начать заново, нажав /start.",
    "CANCELLATION_FAILED": "Не удалось отменить бронирование. Возможно, оно уже обработано.",
    # HTML шаблон для экрана выбора курса
    "SELECT_COURSE_DETAILS": (
        "<b>Курс:</b> {course_name}\n"
        "<b>Имя:</b> {first_name}\n"
        "<b>Старт:</b> {start_date}\n"
        "<b>Стоимость:</b> {price_info}\n\n"
        "{description}"
    ),
    # HTML шаблон с реквизитами
    "PAYMENT_DETAILS": (
        "📝 Ваше место на курс '<b>{course_name}</b>' предварительно забронировано (Заявка №<b>{booking_id}</b>).\n\n"
        "⏳ <i>{duration_notice}</i>\n\n"
        "💳 <b>Реквизиты для оплаты:</b>\n\n"
        "🇷🇺 <b>Т-Банк ({price_rub} RUB):</b>\n"
        "  Карта: <code>{tbank_card}</code>\n"
        "  Получатель: {tbank_holder}\n\n"
        "🇰🇿 <b>Kaspi ({price_kzt} KZT):</b>\n"
        "  Карта: <code>{kaspi_card}</code>\n\n"
        "🇦🇷 <b>Аргентина ({price_ars} ARS):</b>\n"
        "  Alias: <code>{ars_alias}</code>\n\n"
        "💸 <b>USDT TRC-20 ({price_usdt} USDT):</b>\n"
        "  Адрес: <code>{usdt_address}</code>\n\n"
        "🧾 После оплаты отправьте фото чека в этот чат."
    )
}

# Админские сообщения
ADMIN = {
    "APPROVED_BADGE": "✅ ОДОБРЕНО - {timestamp}",
    "APPROVAL_FAILED": "⚠️ Не удалось подтвердить заявку №{booking_id}. Возможно, она уже обработана.",
    # Шаблон подтверждения оплаты пользователю после одобрения
    "CONFIRMATION_MESSAGE": (
        "Привет, {first_name}!\n\n"
        "Ты в {stream_title} ({dates_text}).\n\n"
        "Что дальше:\n"
        "1. Первый лайв: {first_live_calendar_link}\n"
        "2. Вступай в группу потока: {group_invite_link}\n\n"
        "По любым вопросам пиши {support_contact}"
    )
}

def get_text(category: str, key: str, **kwargs) -> str:
    """
    Получить текст по категории и ключу

    Args:
        category: Категория текстов (FREE_LESSON, REFERRAL, BOOKING)
        key: Ключ внутри категории
        **kwargs: Параметры для форматирования

    Returns:
        Отформатированный текст
    """
    texts = {
        "FREE_LESSON": FREE_LESSON,
        "REFERRAL": REFERRAL,
        "BOOKING": BOOKING,
        "START": START,
        "RESET": RESET,
        "REFERRAL_ADMIN": REFERRAL_ADMIN,
        "REFERRAL_STATS": REFERRAL_STATS,
        "STATS": STATS,
        "BOOKING_FLOW": BOOKING_FLOW,
        "ADMIN": ADMIN
    }

    category_texts = texts.get(category)
    if category_texts is None:
        try:
            import logging
            logging.getLogger(__name__).error(f"Missing text category: {category}")
        except Exception:
            pass
        return f"[TEXT_NOT_FOUND: {category}.{key}]"
    text = category_texts.get(key)
    if text is None:
        try:
            import logging
            logging.getLogger(__name__).error(f"Missing text key: {category}.{key}")
        except Exception:
            pass
        return f"[TEXT_NOT_FOUND: {category}.{key}]"

    if kwargs:
        return text.format(**kwargs)
    return text
