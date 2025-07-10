# db/events.py
import logging
import json
from psycopg2.extras import DictCursor
from db.base import get_db_connection

logger = logging.getLogger(__name__)

def log_event(user_id, event_type, details=None, username=None, first_name=None):
    """Logs a user event to the events table for statistics."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Создаем details словарь если его нет
            if details is None:
                details = {}
            
            # Добавляем username и first_name если они переданы
            if username:
                details['username'] = username
            if first_name:
                details['first_name'] = first_name
            
            details_json = json.dumps(details) if details else None
            cursor.execute(
                "INSERT INTO events (user_id, event_type, details) VALUES (%s, %s, %s)",
                (user_id, event_type, details_json)
            )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to log event {event_type} for user {user_id}: {e}")
    finally:
        conn.close()

def get_stats_summary():
    """Retrieves a summary of statistics for the /stats command."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Уникальные пользователи за сегодня
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM events
                WHERE created_at >= CURRENT_DATE;
            """)
            users_today = cursor.fetchone()['count']

            # Уникальные пользователи за 7 дней
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM events
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days';
            """)
            users_week = cursor.fetchone()['count']

            # Новые бронирования за сегодня
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM bookings
                WHERE created_at >= CURRENT_DATE;
            """)
            bookings_today = cursor.fetchone()['count']

            # Подтвержденные оплаты за 7 дней
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM bookings
                WHERE confirmed = 2 AND created_at >= CURRENT_DATE - INTERVAL '7 days';
            """)
            confirmed_week = cursor.fetchone()['count']

            return {
                "users_today": users_today,
                "users_week": users_week,
                "bookings_today": bookings_today,
                "confirmed_week": confirmed_week
            }
    finally:
        conn.close()