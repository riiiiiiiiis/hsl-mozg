# db/courses.py
from psycopg2.extras import DictCursor
from db.base import get_db_connection

def get_active_courses():
    """Loads all courses where is_active = TRUE."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * FROM courses WHERE is_active = TRUE ORDER BY id ASC")
            return cursor.fetchall()
    finally:
        conn.close()

def get_course_by_id(course_id):
    """Gets information about a specific course by its ID."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
            return cursor.fetchone()
    finally:
        conn.close()