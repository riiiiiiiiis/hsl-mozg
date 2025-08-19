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
        "description": "✌️ ЧЕТВЕРТЫЙ ПОТОК ВАЙБКОДИНГА\n\n\"Я никогда не совалась в программирование. Курс открыл другой мир\" — Радислава\n\"Навайбкодила мужу сайт\" — Настя\n\nНаучитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI\n\n+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения\n\n🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ\n\n📚 ФОРМАТ:\n• Видео-уроки + текстовые материалы\n• 3 лайва с практикой\n• Практические домашки с разбором\n• Доступ к материалам навсегда\n\n🛠 ИСПОЛЬЗУЕМ:\nПоследние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4\nВайбкодерские аппы: Cursor, Windsurf, Bolt, Gemini CLI\n\n💰 CORE:\n• Все материалы и записи\n• Закрытый чат с поддержкой\n• Обратная связь по домашкам\n\n📅 Старт: 1 сентября\n⏰ Занятия по средам в 21:00 по мск (каждую неделю)\n\nОплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек.",
        "price_usd": 150,                           # Price in US dollars
        
        # Optional fields (defaults provided if missing):
        "price_usd_cents": 10000,                   # Price in cents (auto-calculated if missing)
        "is_active": True,                          # Whether course is available for booking
        "start_date_text": "1 сентября",               # Human-readable start date
    }
]

# To add a new course:
# 1. Add a new dictionary to the COURSES list above
# 2. Ensure all required fields are present (id, name, button_text, description, price_usd)
# 3. Optional fields will be auto-populated if missing
# 4. Run tests to verify data consistency: python3 test_courses.py

CALENDAR_LINK = "https://calendar.app.google/gYhZNcreyWrAuEgT9"
BOOKING_DURATION_NOTICE = "Ваше место предварительно забронировано на 1 час. Пожалуйста, произведите оплату и отправьте фото чека в этот чат для подтверждения."


# --- Free Lessons Configuration ---

# Import datetime for lesson scheduling
from datetime import datetime

# Multiple free lessons configuration - hardcoded for simplicity
FREE_LESSONS = {
    'cursor_lesson': {
        'id': 1,  # For callback_data
        'title': 'Вайбкодинг с Cursor',
        'button_text': '🆓 Вайбкодинг с Cursor',
        'description': '🎯 ВАЙБКОДИНГ С CURSOR\n\n'
                      'Узнайте, как создавать сайты и приложения с помощью Cursor - самого мощного AI-редактора для программирования!\n\n'
                      '📚 ЧТО БУДЕТ НА УРОКЕ:\n'
                      '• Знакомство с Cursor и его возможностями\n'
                      '• Создание полноценного веб-приложения за 60 минут\n'
                      '• Практические приёмы работы с AI в Cursor\n'
                      '• Ответы на ваши вопросы\n'
                      '⏰ Длительность: 90 минут\n'
                      '👥 Формат: онлайн\n'
                      '📅 Дата: 2 сентября в 21:00 по МСК\n'
                      '🔗 Ссылка на видеовстречу будет отправлена сюда за 15 минут перед началом урока',
        'datetime': datetime(2025, 9, 2, 21, 0, 0),  # For notification scheduling
        'is_active': True,
        'reminder_text': '🎯 Урок по Cursor уже скоро!\n\n{description}\n\n🔗 Ссылка на урок: https://calendar.app.google/RpsZQ415YzLPuQvJ7\n\nУвидимся на уроке! 👋'
    },
    'vibecoding_lesson': {
        'id': 2,  # For callback_data
        'title': 'Основы вайбкодинга',
        'button_text': '🆓 Основы вайбкодинга',
        'description': '🎯 ОСНОВЫ ВАЙБКОДИНГА\n\n'
                      'Познакомьтесь с основами вайбкодинга и научитесь создавать проекты с помощью AI!\n\n'
                      '📚 ЧТО БУДЕТ НА УРОКЕ:\n'
                      '• Введение в вайбкодинг\n'
                      '• Практические примеры\n'
                      '• Работа с AI-инструментами\n'
                      '• Ответы на вопросы\n'
                      '⏰ Длительность: 90 минут\n'
                      '👥 Формат: онлайн\n'
                      '📅 Дата: 5 сентября в 19:00 по МСК\n'
                      '🔗 Ссылка на видеовстречу будет отправлена сюда за 15 минут перед началом урока',
        'datetime': datetime(2025, 9, 5, 19, 0, 0),  # For notification scheduling
        'is_active': True,
        'reminder_text': '🎯 Урок по вайбкодингу начинается!\n\n{description}\n\nУвидимся на уроке! 👋'
    }
}

# Helper functions for FREE_LESSONS
def get_lesson_by_id(lesson_id):
    """Find lesson by ID and return lesson_type and lesson_data"""
    for lesson_type, lesson_data in FREE_LESSONS.items():
        if lesson_data['id'] == lesson_id:
            return lesson_type, lesson_data
    return None, None

def get_active_lessons():
    """Get all active lessons"""
    return {k: v for k, v in FREE_LESSONS.items() if v.get('is_active', False)}

def get_lesson_by_type(lesson_type):
    """Get lesson data by lesson_type"""
    return FREE_LESSONS.get(lesson_type)

# Free lesson messages
FREE_LESSON_EMAIL_REQUEST = "📧 Для записи на бесплатный урок введите ваш email адрес:"
FREE_LESSON_EMAIL_INVALID = "❌ Неверный формат email. Пожалуйста, введите корректный email адрес (например: example@mail.com)"
FREE_LESSON_REGISTRATION_SUCCESS = "✅ Отлично! Вы записаны на бесплатный урок.\n\n📅 Дата: {date}\n📧 Email: {email}\n\n🔔 Ссылка на видеовстречу будет отправлена сюда за 15 минут перед началом урока."
FREE_LESSON_ALREADY_REGISTERED = "ℹ️ Вы уже зарегистрированы на бесплатный урок.\n\n📅 Дата: {date}\n🔔 Ссылка будет отправлена перед началом."
FREE_LESSON_REMINDER = "🎯 Бесплатный урок уже скоро!\n\n📅 {date}\n� Ссыл ка: {link}\n\nУвидимся на уроке! 👋"


# --- Callback Data ---

CALLBACK_RESERVE_SPOT = "reserve_spot"
CALLBACK_SELECT_COURSE_PREFIX = "select_course_"
CALLBACK_CONFIRM_COURSE_SELECTION = "confirm_course_selection_v2"
CALLBACK_BACK_TO_COURSE_SELECTION = "back_to_course_selection"
CALLBACK_ADMIN_APPROVE_PAYMENT = "admin_approve_"
CALLBACK_ADMIN_REJECT_PAYMENT = "admin_reject_"
CALLBACK_CANCEL_RESERVATION = "cancel_reservation"

# New free lesson callbacks for multiple lessons
CALLBACK_FREE_LESSON_PREFIX = "free_lesson_"
CALLBACK_FREE_LESSON_REGISTER_PREFIX = "free_lesson_register_"

# Legacy callbacks - will be removed
# CALLBACK_FREE_LESSON_INFO = "free_lesson_info"  # deprecated
# CALLBACK_FREE_LESSON_REGISTER = "free_lesson_register"  # deprecated


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