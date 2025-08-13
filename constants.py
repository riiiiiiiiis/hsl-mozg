# --- Courses and Static Links ---

# Course data structure - hardcoded course information previously stored in database
# This allows for easier content management and formatting without database access
# All course data is validated on first access via db/course_validation.py
COURSES = [
    {
        # Required fields (validated by course_validation.py):
        "id": 1,                                    # Unique course identifier (positive integer)
        "name": "Вайб кодинг",                      # Course display name
        "button_text": "Вайб-кодинг: реализация продуктовых идей",  # Text shown on selection button
        "description": "✌️ ТРЕТИЙ ПОТОК ВАЙБКОДИНГА\n\n\"Я никогда не совалась в программирование. Курс открыл другой мир\" — Радислава\n\"Навайбкодила мужу сайт\" — Настя\n\nНаучитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI\n\n+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения\n\n🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ\n\n📚 ФОРМАТ:\n• Видео-уроки + текстовые материалы\n• 3 лайва с практикой\n• Практические домашки с разбором\n• Доступ к материалам навсегда\n\n🛠 ИСПОЛЬЗУЕМ:\nПоследние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4\nВайбкодерские аппы: Cursor, Windsurf, Bolt, Gemini CLI\n\n💰 CORE:\n• Все материалы и записи\n• Закрытый чат с поддержкой\n• Обратная связь по домашкам\n\n📅 Старт: 12 августа\n⏰ Занятия по средам в 21:00 по мск\n\nОплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек.",
        "price_usd": 150,                           # Price in US dollars
        
        # Optional fields (defaults provided if missing):
        "price_usd_cents": 10000,                   # Price in cents (auto-calculated if missing)
        "is_active": True,                          # Whether course is available for booking
        "start_date_text": "12 августа",               # Human-readable start date
    },
    {
        # EXTRA tier course with additional features
        "id": 2,
        "name": "Вайб кодинг EXTRA",
        "button_text": "Вайб Кодинг EXTRA - $200", 
        "description": "✌️ ТРЕТИЙ ПОТОК ВАЙБКОДИНГА (РАСШИРЕННЫЙ)\n\n\"Я никогда не совалась в программирование. Курс открыл другой мир\" — Радислава\n\"Навайбкодила мужу сайт\" — Настя\n\nНаучитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI\n\n+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения\n\n🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ\n\n📚 ФОРМАТ:\n• Видео-уроки + текстовые материалы\n• 3 лайва с практикой\n• Практические домашки с разбором\n• Доступ к материалам навсегда\n\n🛠 ИСПОЛЬЗУЕМ:\nПоследние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4\nВайбкодерские аппы: Cursor, Windsurf, Bolt, Gemini CLI\n\n⭐ EXTRA ($200):\n• Всё из базового CORE +\n• Доступ в личку на время курса\n• Индивидуальное занятие после окончания\n\n📅 Старт: 12 августа\n⏰ Занятия по средам в 21:00 по мск\n\nОплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек.",
        "price_usd": 200,
        "price_usd_cents": 20000,
        "is_active": False,
        "start_date_text": "12 августа",
    }
]

# To add a new course:
# 1. Add a new dictionary to the COURSES list above
# 2. Ensure all required fields are present (id, name, button_text, description, price_usd)
# 3. Optional fields will be auto-populated if missing
# 4. Run tests to verify data consistency: python3 test_courses.py

CALENDAR_LINK = "https://calendar.app.google/gYhZNcreyWrAuEgT9"
BOOKING_DURATION_NOTICE = "Ваше место предварительно забронировано на 1 час. Пожалуйста, произведите оплату и отправьте фото чека в этот чат для подтверждения."


# --- Free Lesson Configuration ---

# Free lesson information - hardcoded for simplicity
FREE_LESSON = {
    "title": "Бесплатный первый урок",
    "button_text": "🆓 Бесплатный первый урок",
    "description": "🎯 БЕСПЛАТНЫЙ ПЕРВЫЙ УРОК ВАЙБКОДИНГА\n\n"
                   "Узнайте, как создавать сайты и приложения с помощью AI, даже если вы никогда не программировали!\n\n"
                   "📚 ЧТО БУДЕТ НА УРОКЕ:\n"
                   "• Знакомство с AI-инструментами для разработки\n"
                   "• Создание простого сайта за 30 минут\n"
                   "• Ответы на ваши вопросы\n"
                   "• Обзор полного курса\n\n"
                   "🎁 БОНУС: получите доступ к материалам урока навсегда\n\n"
                   "⏰ Длительность: 60 минут\n"
                   "👥 Формат: онлайн в Google Meet",
    "date_text": "13 августа в 21:00 по МСК",
    "google_meet_link": "https://meet.google.com/abc-defg-hij",
    "is_active": True
}

# Free lesson messages
FREE_LESSON_EMAIL_REQUEST = "📧 Для записи на бесплатный урок введите ваш email адрес:"
FREE_LESSON_EMAIL_INVALID = "❌ Неверный формат email. Пожалуйста, введите корректный email адрес (например: example@mail.com)"
FREE_LESSON_REGISTRATION_SUCCESS = "✅ Отлично! Вы записаны на бесплатный урок.\n\n📅 Дата: {date}\n📧 Email: {email}\n\n🔔 Ссылка на урок будет отправлена за 15 минут до начала."
FREE_LESSON_ALREADY_REGISTERED = "ℹ️ Вы уже зарегистрированы на бесплатный урок.\n\n📅 Дата: {date}\n🔔 Ссылка будет отправлена за 15 минут до начала."
FREE_LESSON_REMINDER = "🎯 Бесплатный урок начинается через 15 минут!\n\n📅 {date}\n🔗 Ссылка: {link}\n\nУвидимся на уроке! 👋"


# --- Callback Data ---

CALLBACK_RESERVE_SPOT = "reserve_spot"
CALLBACK_SELECT_COURSE_PREFIX = "select_course_"
CALLBACK_CONFIRM_COURSE_SELECTION = "confirm_course_selection_v2"
CALLBACK_BACK_TO_COURSE_SELECTION = "back_to_course_selection"
CALLBACK_ADMIN_APPROVE_PAYMENT = "admin_approve_"
CALLBACK_ADMIN_REJECT_PAYMENT = "admin_reject_"
CALLBACK_CANCEL_RESERVATION = "cancel_reservation"
CALLBACK_FREE_LESSON_INFO = "free_lesson_info"
CALLBACK_FREE_LESSON_REGISTER = "free_lesson_register"


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