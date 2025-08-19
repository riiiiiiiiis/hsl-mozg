"""
Критические константы, которые используются во многих местах
Большая часть контента перенесена в:
- data/courses.yaml - курсы
- data/lessons.yaml - бесплатные уроки  
- locales/ru.py - тексты сообщений
- config.py - конфигурация реферальной системы
- handlers/callbacks.py - callback константы
"""

# Обратная совместимость для старого кода
# TODO: Постепенно удалить после полного рефакторинга

# Временные импорты для обратной совместимости
from utils.lessons import (
    get_all_lessons as _get_all_lessons,
    get_active_lessons,
    get_lesson_by_id,
    get_lesson_by_type
)
from utils.courses import (
    get_all_courses as _get_all_courses
)
from handlers.callbacks import *
from locales.ru import get_text
import config

# Для обратной совместимости - загрузка данных при импорте
FREE_LESSONS = _get_all_lessons()
COURSES = _get_all_courses()

# Тексты для обратной совместимости
FREE_LESSON_EMAIL_REQUEST = get_text("FREE_LESSON", "EMAIL_REQUEST")
FREE_LESSON_EMAIL_INVALID = get_text("FREE_LESSON", "EMAIL_INVALID")
FREE_LESSON_REGISTRATION_SUCCESS = get_text("FREE_LESSON", "REGISTRATION_SUCCESS")
FREE_LESSON_ALREADY_REGISTERED = get_text("FREE_LESSON", "ALREADY_REGISTERED")
FREE_LESSON_REMINDER = get_text("FREE_LESSON", "REMINDER")

REFERRAL_APPLIED_MESSAGE = get_text("REFERRAL", "APPLIED")
REFERRAL_EXPIRED_MESSAGE = get_text("REFERRAL", "EXPIRED")
REFERRAL_ALREADY_USED_MESSAGE = get_text("REFERRAL", "ALREADY_USED")

BOOKING_DURATION_NOTICE = get_text("BOOKING", "DURATION_NOTICE")
CALENDAR_LINK = get_text("BOOKING", "CALENDAR_LINK")

# Реферальная конфигурация для обратной совместимости
REFERRAL_DISCOUNTS = config.REFERRAL_DISCOUNTS
REFERRAL_BOT_URL = config.REFERRAL_BOT_URL
REFERRAL_START_PARAMETER = config.REFERRAL_START_PARAMETER
REFERRAL_CODE_LENGTH = config.REFERRAL_CODE_LENGTH
REFERRAL_CODE_CHARS = config.REFERRAL_CODE_CHARS
REFERRAL_ADMIN_IDS = config.REFERRAL_ADMIN_IDS
REFERRAL_TABLE_NAME = config.REFERRAL_TABLE_NAME
REFERRAL_USAGE_TABLE_NAME = config.REFERRAL_USAGE_TABLE_NAME