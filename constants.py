# --- Courses and Static Links ---

COURSES = [
    {
        "id": "1", 
        "button_text": "Вайб Кодинг CORE - $100",
        "name": "Вайб кодинг",
        "price_usd": 100,
        "description": "✌️ ВТОРОЙ ПОТОК ВАЙБКОДИНГА\n\n\"Я никогда не совалась в программирование. Курс открыл другой мир\" — Радислава\n\"Навайбкодила мужу сайт\" — Настя\n\nНаучитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI\n\n+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения\n\n🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ\n\n📚 ФОРМАТ:\n• Видео-уроки + текстовые материалы\n• 3 лайва с практикой\n• Практические домашки с разбором\n• Доступ к материалам навсегда\n\n🛠 ИСПОЛЬЗУЕМ:\nПоследние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4\nВайбкодерские аппы: Cursor, Windsurf, Bolt, Gemini CLI\n\n💰 CORE ($100):\n• Все материалы и записи\n• Закрытый чат с поддержкой\n• Обратная связь по домашкам\n\n📅 Старт: 23 июля\n⏰ Занятия по средам в 21:00 по мск\n\nОплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек."
    },
    {
        "id": "2",
        "button_text": "Вайб Кодинг EXTRA - $200", 
        "name": "Вайб кодинг EXTRA",
        "price_usd": 200,
        "description": "✌️ ВТОРОЙ ПОТОК ВАЙБКОДИНГА (РАСШИРЕННЫЙ)\n\n\"Я никогда не совалась в программирование. Курс открыл другой мир\" — Радислава\n\"Навайбкодила мужу сайт\" — Настя\n\nНаучитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI\n\n+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения\n\n🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ\n\n📚 ФОРМАТ:\n• Видео-уроки + текстовые материалы\n• 3 лайва с практикой\n• Практические домашки с разбором\n• Доступ к материалам навсегда\n\n🛠 ИСПОЛЬЗУЕМ:\nПоследние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4\nВайбкодерские аппы: Cursor, Windsurf, Bolt, Gemini CLI\n\n⭐ EXTRA ($200):\n• Всё из базового CORE +\n• Доступ в личку на время курса\n• Индивидуальное занятие после окончания\n\n📅 Старт: 23 июля\n⏰ Занятия по средам в 21:00 по мск\n\nОплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек."
    }
]

CALENDAR_LINK = "https://calendar.app.google/gYhZNcreyWrAuEgT9"
BOOKING_DURATION_NOTICE = "Ваше место предварительно забронировано на 1 час. Пожалуйста, произведите оплату и отправьте фото чека в этот чат для подтверждения."


# --- Callback Data ---

CALLBACK_RESERVE_SPOT = "reserve_spot"
CALLBACK_SELECT_COURSE_PREFIX = "select_course_"
CALLBACK_CONFIRM_COURSE_SELECTION = "confirm_course_selection_v2"
CALLBACK_BACK_TO_COURSE_SELECTION = "back_to_course_selection"
CALLBACK_ADMIN_APPROVE_PAYMENT = "admin_approve_"
CALLBACK_ADMIN_REJECT_PAYMENT = "admin_reject_"
CALLBACK_CANCEL_RESERVATION = "cancel_reservation"


# --- Referral System Configuration ---

# Available discount percentages and their default activation limits
REFERRAL_DISCOUNTS = {
    10: {
        "default_activations": 50,
        "description": "10% скидка"
    },
    20: {
        "default_activations": 20,
        "description": "20% скидка"
    },
    30: {
        "default_activations": 10,
        "description": "30% скидка"
    },
    50: {
        "default_activations": 5,
        "description": "50% скидка"
    },
    100: {
        "default_activations": 1,
        "description": "100% скидка (бесплатно)"
    },
}

# Referral link parameters
REFERRAL_BOT_URL = "https://t.me/"
REFERRAL_START_PARAMETER = "ref_"

# Referral code generation settings
REFERRAL_CODE_LENGTH = 8
REFERRAL_CODE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Admin restrictions (empty means any admin can create)
REFERRAL_ADMIN_IDS = []

# Database table names
REFERRAL_TABLE_NAME = "referral_coupons"
REFERRAL_USAGE_TABLE_NAME = "referral_usage"

# Messages
REFERRAL_APPLIED_MESSAGE = "🎉 Применен купон на {discount}% скидку!"
REFERRAL_EXPIRED_MESSAGE = "❌ К сожалению, этот купон больше не активен."
REFERRAL_ALREADY_USED_MESSAGE = "❌ Вы уже использовали этот купон ранее."