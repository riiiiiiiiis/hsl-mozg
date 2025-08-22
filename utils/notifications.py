# utils/notifications.py
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from telegram.ext import Application
import constants
from db import free_lessons as db_free_lessons
from db import events as db_events

logger = logging.getLogger(__name__)

async def schedule_all_lesson_notifications(application: Application):
    """
    Планирует уведомления для всех активных уроков при старте бота.
    Не использует force_send - только точное планирование по времени.
    """
    active_lessons = constants.get_active_lessons()
    
    if not active_lessons:
        logger.info("No active lessons found for notification scheduling")
        return
    
    logger.info(f"Found {len(active_lessons)} active lessons, scheduling notifications...")
    
    for lesson_type, lesson_data in active_lessons.items():
        try:
            await schedule_lesson_notification(application, lesson_type, lesson_data)
        except Exception as e:
            logger.error(f"Error scheduling notification for lesson {lesson_type}: {e}")

async def schedule_lesson_notification(application: Application, lesson_type: str, lesson_data: dict):
    """
    Планирует уведомление за 15 минут до урока для конкретного типа урока.
    """
    lesson_datetime = lesson_data['datetime']
    notification_time = lesson_datetime - timedelta(minutes=15)
    current_time = datetime.now(timezone.utc)
    
    # Преобразуем lesson_datetime и notification_time в UTC если нужно
    if lesson_datetime.tzinfo is None:
        lesson_datetime = lesson_datetime.replace(tzinfo=timezone.utc)
    else:
        lesson_datetime = lesson_datetime.astimezone(timezone.utc)
    
    if notification_time.tzinfo is None:
        notification_time = notification_time.replace(tzinfo=timezone.utc)
    else:
        notification_time = notification_time.astimezone(timezone.utc)
    
    if notification_time <= current_time:
        logger.info(f"Notification time for {lesson_type} has already passed (was at {notification_time})")
        return
    
    delay_seconds = (notification_time - current_time).total_seconds()
    delay_minutes = delay_seconds / 60
    
    logger.info(f"Scheduled notification for {lesson_type} in {delay_minutes:.1f} minutes "
                f"(at {notification_time.strftime('%Y-%m-%d %H:%M')})")
    
    # Создаем асинхронную задачу для отправки уведомления
    asyncio.create_task(delayed_notification(application, lesson_type, lesson_data, delay_seconds))

async def delayed_notification(application: Application, lesson_type: str, lesson_data: dict, delay_seconds: float):
    """
    Отправляет уведомления через заданное время.
    """
    try:
        await asyncio.sleep(delay_seconds)
        logger.info(f"Sending notifications for lesson {lesson_type}")
        await send_notifications_for_lesson(application, lesson_type, lesson_data)
    except asyncio.CancelledError:
        logger.info(f"Notification task for {lesson_type} was cancelled")
    except Exception as e:
        logger.error(f"Error in delayed notification for {lesson_type}: {e}")

async def send_notifications_for_lesson(application: Application, lesson_type: str, lesson_data: dict):
    """
    Отправляет уведомления всем зарегистрированным пользователям на конкретный тип урока.
    """
    # Получаем всех зарегистрированных пользователей для данного типа урока
    registrations = db_free_lessons.get_registrations_by_type(lesson_type)
    
    if not registrations:
        logger.info(f"No registrations found for lesson {lesson_type}")
        return
    
    logger.info(f"Found {len(registrations)} registrations for lesson {lesson_type}")
    
    # Фильтруем только тех, кому еще не отправили уведомления
    pending_registrations = [reg for reg in registrations if not reg.get('notification_sent', False)]
    
    if not pending_registrations:
        logger.info(f"All users for lesson {lesson_type} have already received notifications")
        return
    
    logger.info(f"Sending notifications to {len(pending_registrations)} users for lesson {lesson_type}")
    
    # Формируем текст уведомления
    reminder_text = lesson_data['reminder_text'].format(
        description=lesson_data['description']
    )
    
    successful_sends = 0
    failed_sends = 0
    
    for registration in pending_registrations:
        try:
            # Отправляем уведомление
            await application.bot.send_message(
                chat_id=registration['user_id'],
                text=reminder_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            # Помечаем уведомление как отправленное
            db_free_lessons.mark_notification_sent(registration['id'])
            
            # Логируем успешную отправку
            db_events.log_event(
                registration['user_id'],
                'free_lesson_reminder_sent',
                details={
                    'lesson_type': lesson_type,
                    'registration_id': registration['id']
                },
                username=registration.get('username'),
                first_name=registration.get('first_name')
            )
            
            successful_sends += 1
            logger.info(f"Sent notification for {lesson_type} to user {registration['user_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send notification for {lesson_type} to user {registration['user_id']}: {e}")
            failed_sends += 1
    
    logger.info(f"Notification summary for {lesson_type}: {successful_sends} successful, {failed_sends} failed")

def get_time_until_lesson(lesson_type: str) -> float:
    """
    Возвращает время до начала урока в минутах для конкретного типа урока.
    Возвращает None, если урок не найден или уже прошел.
    """
    lesson_data = constants.get_lesson_by_type(lesson_type)
    if not lesson_data:
        return None
    
    lesson_datetime = lesson_data['datetime']
    current_time = datetime.now(timezone.utc)
    
    # Преобразуем lesson_datetime в UTC если нужно
    if lesson_datetime.tzinfo is None:
        lesson_datetime = lesson_datetime.replace(tzinfo=timezone.utc)
    else:
        lesson_datetime = lesson_datetime.astimezone(timezone.utc)
    
    time_until_lesson = lesson_datetime - current_time
    minutes_until = time_until_lesson.total_seconds() / 60
    
    return minutes_until if minutes_until > 0 else 0

def is_lesson_active(lesson_type: str) -> bool:
    """
    Проверяет, активен ли урок (не прошел ли он уже).
    """
    lesson_data = constants.get_lesson_by_type(lesson_type)
    if not lesson_data:
        return False
    
    # Проверяем флаг активности в константах
    if not lesson_data.get('is_active', False):
        return False
    
    # Проверяем, не прошло ли время урока
    lesson_datetime = lesson_data['datetime']
    current_time = datetime.now(timezone.utc)
    
    # Преобразуем lesson_datetime в UTC если нужно
    if lesson_datetime.tzinfo is None:
        lesson_datetime = lesson_datetime.replace(tzinfo=timezone.utc)
    else:
        lesson_datetime = lesson_datetime.astimezone(timezone.utc)
    
    # Урок считается активным, если он еще не начался или идет сейчас (+ 2 часа на проведение)
    lesson_end_time = lesson_datetime + timedelta(hours=2)
    
    return current_time < lesson_end_time

def get_notification_status() -> dict:
    """
    Возвращает статус уведомлений для всех активных уроков.
    Полезно для мониторинга и отладки.
    """
    status = {}
    active_lessons = constants.get_active_lessons()
    
    for lesson_type, lesson_data in active_lessons.items():
        lesson_datetime = lesson_data['datetime']
        notification_time = lesson_datetime - timedelta(minutes=15)
        current_time = datetime.now(timezone.utc)
        
        # Преобразуем lesson_datetime и notification_time в UTC если нужно
        if lesson_datetime.tzinfo is None:
            lesson_datetime = lesson_datetime.replace(tzinfo=timezone.utc)
        else:
            lesson_datetime = lesson_datetime.astimezone(timezone.utc)
        
        if notification_time.tzinfo is None:
            notification_time = notification_time.replace(tzinfo=timezone.utc)
        else:
            notification_time = notification_time.astimezone(timezone.utc)
        
        time_until_notification = (notification_time - current_time).total_seconds() / 60
        time_until_lesson = (lesson_datetime - current_time).total_seconds() / 60
        
        status[lesson_type] = {
            'lesson_title': lesson_data['title'],
            'lesson_datetime': lesson_datetime.strftime('%Y-%m-%d %H:%M'),
            'notification_datetime': notification_time.strftime('%Y-%m-%d %H:%M'),
            'minutes_until_notification': max(0, time_until_notification),
            'minutes_until_lesson': max(0, time_until_lesson),
            'notification_passed': time_until_notification <= 0,
            'lesson_passed': time_until_lesson <= 0,
            'is_active': lesson_data.get('is_active', False)
        }
    
    return status

# Admin function for manual notification testing
async def send_test_notification(application: Application, lesson_type: str, user_id: int = None):
    """
    Отправляет тестовое уведомление для конкретного урока.
    Если user_id указан, отправляет только этому пользователю.
    """
    lesson_data = constants.get_lesson_by_type(lesson_type)
    if not lesson_data:
        logger.error(f"Lesson type {lesson_type} not found")
        return False
    
    if user_id:
        # Отправка конкретному пользователю
        try:
            reminder_text = f"🧪 ТЕСТ: {lesson_data['reminder_text']}".format(
                description=lesson_data['description']
            )
            await application.bot.send_message(
                chat_id=user_id,
                text=reminder_text,
                parse_mode='HTML'
            )
            logger.info(f"Test notification sent to user {user_id} for lesson {lesson_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to send test notification to user {user_id}: {e}")
            return False
    else:
        # Отправка всем зарегистрированным
        logger.info(f"Sending test notifications for lesson {lesson_type} to all registered users")
        await send_notifications_for_lesson(application, lesson_type, lesson_data)
        return True