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
        "BOOKING": BOOKING
    }
    
    category_texts = texts.get(category, {})
    text = category_texts.get(key, "")
    
    if kwargs:
        return text.format(**kwargs)
    return text