# utils/notifications.py
import logging
from datetime import datetime, timedelta
from telegram.ext import Application
import constants
from db import free_lessons as db_free_lessons
from db import events as db_events

logger = logging.getLogger(__name__)

def parse_lesson_datetime():
    """
    Парсит дату и время урока из константы.
    Возвращает datetime объект или None, если не удалось распарсить.
    """
    try:
        # Пример: "15 августа в 19:00 по МСК"
        date_text = constants.FREE_LESSON['date_text']
        
        # Простой парсинг для примера - в реальном проекте лучше использовать более надёжный парсер
        # Для демонстрации используем фиксированную дату
        # В реальном проекте здесь должен быть полноценный парсер даты
        
        # Временное решение: возвращаем фиксированную дату для тестирования
        # 13 августа 2025 в 21:00 МСК
        lesson_datetime = datetime(2025, 8, 13, 21, 0, 0)
        return lesson_datetime
    except Exception as e:
        logger.error(f"Error parsing lesson datetime: {e}")
        return None

def should_send_notification():
    """
    Проверяет, нужно ли отправлять уведомления сейчас.
    Возвращает True, если до урока осталось 15 минут.
    """
    lesson_datetime = parse_lesson_datetime()
    if not lesson_datetime:
        return False
    
    current_time = datetime.now()
    time_until_lesson = lesson_datetime - current_time
    
    # Проверяем, что до урока осталось от 14 до 16 минут (окно в 2 минуты для надёжности)
    minutes_until = time_until_lesson.total_seconds() / 60
    return 14 <= minutes_until <= 16

async def send_lesson_reminders(application: Application, force_send=False):
    """
    Отправляет напоминания о бесплатном уроке всем зарегистрированным пользователям.
    
    Args:
        application: Telegram Application instance
        force_send: Если True, отправляет уведомления независимо от времени
    """
    if not force_send and not should_send_notification():
        return
    
    # Получаем всех пользователей, которым ещё не отправили уведомление
    registrations = db_free_lessons.get_all_registrations_for_notification()
    
    if not registrations:
        logger.info("No users to notify for free lesson")
        return
    
    logger.info(f"Sending free lesson reminders to {len(registrations)} users")
    
    # Формируем сообщение с напоминанием
    reminder_message = constants.FREE_LESSON_REMINDER.format(
        date=constants.FREE_LESSON['date_text'],
        link=constants.FREE_LESSON['google_meet_link']
    )
    
    successful_sends = 0
    failed_sends = 0
    
    for registration in registrations:
        try:
            # Отправляем сообщение пользователю
            await application.bot.send_message(
                chat_id=registration['user_id'],
                text=reminder_message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            # Помечаем уведомление как отправленное
            db_free_lessons.mark_notification_sent(registration['id'])
            
            # Логируем отправку уведомления
            db_events.log_event(
                registration['user_id'],
                'free_lesson_reminder_sent',
                details={'registration_id': registration['id']},
                username=registration.get('username'),
                first_name=registration.get('first_name')
            )
            
            successful_sends += 1
            logger.info(f"Sent free lesson reminder to user {registration['user_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send free lesson reminder to user {registration['user_id']}: {e}")
            failed_sends += 1
    
    logger.info(f"Free lesson reminders sent: {successful_sends} successful, {failed_sends} failed")

def get_time_until_lesson():
    """
    Возвращает время до начала урока в минутах.
    Возвращает None, если не удалось определить время урока.
    """
    lesson_datetime = parse_lesson_datetime()
    if not lesson_datetime:
        return None
    
    current_time = datetime.now()
    time_until_lesson = lesson_datetime - current_time
    minutes_until = time_until_lesson.total_seconds() / 60
    
    return minutes_until if minutes_until > 0 else 0

def is_lesson_active():
    """
    Проверяет, активен ли урок (не прошёл ли он уже).
    """
    lesson_datetime = parse_lesson_datetime()
    if not lesson_datetime:
        return constants.FREE_LESSON.get('is_active', False)
    
    current_time = datetime.now()
    # Урок считается активным, если он ещё не начался или идёт сейчас (+ 2 часа на проведение)
    lesson_end_time = lesson_datetime + timedelta(hours=2)
    
    return current_time < lesson_end_time