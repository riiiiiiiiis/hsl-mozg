# db/free_lessons.py
import logging
import re
from psycopg2.extras import DictCursor
from db.base import get_db_connection

logger = logging.getLogger(__name__)

def validate_email(email):
    """Validates email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_free_lesson_registration(user_id, username, first_name, email, lesson_type='cursor_lesson'):
    """Creates a new free lesson registration with lesson type."""
    if not validate_email(email):
        logger.warning(f"Invalid email format: {email}")
        return False
    
    # Validate lesson_type
    valid_lesson_types = ['cursor_lesson', 'vibecoding_lesson']
    if lesson_type not in valid_lesson_types:
        logger.warning(f"Invalid lesson_type: {lesson_type}. Using default 'cursor_lesson'")
        lesson_type = 'cursor_lesson'
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                INSERT INTO free_lesson_registrations (user_id, username, first_name, email, lesson_type)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    email = EXCLUDED.email,
                    lesson_type = EXCLUDED.lesson_type,
                    registered_at = CURRENT_TIMESTAMP,
                    notification_sent = FALSE
                RETURNING id;
            """, (user_id, username, first_name, email, lesson_type))
            
            registration_id = cur.fetchone()['id']
            conn.commit()
            logger.info(f"Free lesson registration created/updated for user {user_id}, lesson_type: {lesson_type}, registration ID: {registration_id}")
            return registration_id
    except Exception as e:
        logger.error(f"Error creating free lesson registration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_registration_by_user(user_id):
    """Gets free lesson registration by user ID."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT * FROM free_lesson_registrations 
                WHERE user_id = %s
            """, (user_id,))
            
            result = cur.fetchone()
            return dict(result) if result else None
    except Exception as e:
        logger.error(f"Error getting free lesson registration for user {user_id}: {e}")
        return None
    finally:
        conn.close()

def is_user_registered(user_id):
    """Checks if user is already registered for free lesson."""
    registration = get_registration_by_user(user_id)
    return registration is not None

def get_all_registrations_for_notification():
    """Gets all registrations that haven't received notification yet."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT * FROM free_lesson_registrations 
                WHERE notification_sent = FALSE
                ORDER BY registered_at ASC
            """)
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting registrations for notification: {e}")
        return []
    finally:
        conn.close()

def mark_notification_sent(registration_id):
    """Marks notification as sent for a registration."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE free_lesson_registrations 
                SET notification_sent = TRUE 
                WHERE id = %s
            """, (registration_id,))
            
            conn.commit()
            logger.info(f"Marked notification as sent for registration {registration_id}")
            return True
    except Exception as e:
        logger.error(f"Error marking notification as sent for registration {registration_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_registration_count():
    """Gets total count of free lesson registrations."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM free_lesson_registrations")
            count = cur.fetchone()[0]
            return count
    except Exception as e:
        logger.error(f"Error getting registration count: {e}")
        return 0
    finally:
        conn.close()

def get_registrations_by_type(lesson_type):
    """Gets registrations filtered by lesson type."""
    valid_lesson_types = ['cursor_lesson', 'vibecoding_lesson']
    if lesson_type not in valid_lesson_types:
        logger.warning(f"Invalid lesson_type: {lesson_type}")
        return []
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT * FROM free_lesson_registrations 
                WHERE lesson_type = %s
                ORDER BY registered_at ASC
            """, (lesson_type,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting registrations by type {lesson_type}: {e}")
        return []
    finally:
        conn.close()

def get_registration_stats():
    """Gets registration statistics grouped by lesson type."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT 
                    lesson_type,
                    COUNT(*) as total_registrations,
                    COUNT(CASE WHEN notification_sent = TRUE THEN 1 END) as notifications_sent,
                    COUNT(CASE WHEN notification_sent = FALSE THEN 1 END) as pending_notifications
                FROM free_lesson_registrations 
                GROUP BY lesson_type
                ORDER BY lesson_type
            """)
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting registration statistics: {e}")
        return []
    finally:
        conn.close()

def get_all_registrations_with_type():
    """Gets all registrations with lesson type information for admin interface."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    user_id,
                    username,
                    first_name,
                    email,
                    lesson_type,
                    registered_at,
                    notification_sent
                FROM free_lesson_registrations 
                ORDER BY registered_at DESC
            """)
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting all registrations with type: {e}")
        return []
    finally:
        conn.close()