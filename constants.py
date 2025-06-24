# --- Courses and Static Links ---

COURSES = [
    {
        "id": "1",
        "button_text": "Вайб Кодинг",
        "name": "Вайб кодинг",
        "price_usd": 150,
        "description": "На этом курсе в течение двух недель я учу превращать идеи в рабочие прототипы. Программируем на русском языке. Наглядно объясняю как работает ИИ, интернет и приложения. Общение в закрытой группе, домашки, три созвона с записями. Поддержка продолжается месяц после курса.\nПосле обучения ты будешь знать как создавать сайты с помощью ИИ, что такое база данных, как собрать телеграм бота за вечер и выложить проект в интернет. Набор промптов в подарок!\nДля кого: вообще для всех\nДлительность: три недели\nФормат: 3 практических лекции по пятницам в 20:00 МСК в 20:00 МСК\nСтоимость: 150$\nСтарт: 30 мая\n\nОплата возможна переводом на карты Т-Банка, Каспи или в USDT на крипто кошелек.\n\nЧто дальше: После оплаты я добавлю тебя в закрытую группу, где мы будем общаться и делиться материалами. Перед стартом курса пришлю всю необходимую информацию."
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