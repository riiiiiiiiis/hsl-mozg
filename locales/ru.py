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
    # MarkdownV2 шаблон с реквизитами
    "PAYMENT_DETAILS": (
        "📝 Ваше место на курс '*{course_name}*' предварительно забронировано \(Заявка №*{booking_id}*\)\.\n\n"
        "⏳ _{duration_notice}_\n\n"
        "💳 *Реквизиты для оплаты:*\n\n"
        "🇷🇺 *Т\-Банк \({price_rub} RUB\):*\n"
        "  Карта: `{tbank_card}`\n"
        "  Получатель: {tbank_holder}\n\n"
        "🇰🇿 *Kaspi \({price_kzt} KZT\):*\n"
        "  Карта: `{kaspi_card}`\n\n"
        "🇦🇷 *Аргентина \({price_ars} ARS\):*\n"
        "  Alias: `{ars_alias}`\n\n"
        "💸 *USDT TRC\-20 \({price_usdt} USDT\):*\n"
        "  Адрес: `{usdt_address}`\n\n"
        "🧾 После оплаты отправьте фото чека в этот чат\."
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
        "BOOKING_FLOW": BOOKING_FLOW,
        "ADMIN": ADMIN
    }
    
    category_texts = texts.get(category, {})
    text = category_texts.get(key, "")
    
    if kwargs:
        return text.format(**kwargs)
    return text