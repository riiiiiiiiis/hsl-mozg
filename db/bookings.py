# db/bookings.py
from psycopg2.extras import DictCursor
from db.base import get_db_connection
from db import events as db_events

def create_booking(user_id, username, first_name, course_id, referral_code, discount_percent, course_stream='4th_stream'):
    """Creates a new booking record with course stream tracking and returns the new booking ID."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                """INSERT INTO bookings (user_id, username, first_name, course_id, referral_code, discount_percent, course_stream)
                   VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (user_id, username, first_name, course_id, referral_code, discount_percent, course_stream)
            )
            booking_id = cursor.fetchone()['id']
            conn.commit()
            return booking_id
    finally:
        conn.close()

def get_pending_booking_by_user(user_id):
    """Retrieves the most recent pending booking for a user."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT b.id, c.name as course_name, b.confirmed as status
                FROM bookings b
                JOIN courses c ON b.course_id = c.id
                WHERE b.user_id = %s AND b.confirmed = 0
                ORDER BY b.created_at DESC LIMIT 1
            """, (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def get_active_booking_by_user(user_id):
    """Retrieves the most recent active booking (pending or approved) for a user."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT b.id, b.course_id, b.confirmed as status
                FROM bookings b
                WHERE b.user_id = %s AND b.confirmed IN (0, 1, 2)
                ORDER BY b.created_at DESC LIMIT 1
            """, (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def update_booking_status(booking_id, status_code):
    """Updates the 'confirmed' status of a specific booking."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Получаем данные бронирования перед обновлением
            cursor.execute(
                "SELECT user_id, username, first_name, confirmed FROM bookings WHERE id = %s", 
                (booking_id,)
            )
            booking_data = cursor.fetchone()
            
            if not booking_data:
                return False
                
            old_status = booking_data['confirmed']
            cursor.execute("UPDATE bookings SET confirmed = %s WHERE id = %s", (status_code, booking_id))
            
            if cursor.rowcount > 0:
                # Логируем изменение статуса
                status_names = {
                    0: 'pending',
                    1: 'payment_uploaded', 
                    2: 'approved',
                    -1: 'cancelled'
                }
                
                db_events.log_event(
                    booking_data['user_id'],
                    'booking_status_changed',
                    details={
                        'booking_id': booking_id,
                        'old_status': old_status,
                        'new_status': status_code,
                        'old_status_name': status_names.get(old_status, 'unknown'),
                        'new_status_name': status_names.get(status_code, 'unknown')
                    },
                    username=booking_data['username'],
                    first_name=booking_data['first_name']
                )
                
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()

def get_booking_details(booking_id):
    """Retrieves details for a specific booking."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT b.course_id, b.user_id, b.username, b.first_name, b.confirmed, c.name as course_name
                FROM bookings b
                JOIN courses c ON b.course_id = c.id
                WHERE b.id = %s
            """, (booking_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def get_bookings_by_stream(course_stream):
    """Gets bookings filtered by course stream."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT b.*, c.name as course_name
                FROM bookings b
                JOIN courses c ON b.course_id = c.id
                WHERE b.course_stream = %s
                ORDER BY b.created_at DESC
            """, (course_stream,))
            results = cursor.fetchall()
            return [dict(row) for row in results]
    finally:
        conn.close()

def get_booking_stats_by_stream():
    """Gets booking statistics grouped by course stream."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    course_stream,
                    COUNT(*) as total_bookings,
                    COUNT(CASE WHEN confirmed = 0 THEN 1 END) as pending,
                    COUNT(CASE WHEN confirmed = 1 THEN 1 END) as payment_uploaded,
                    COUNT(CASE WHEN confirmed = 2 THEN 1 END) as approved,
                    COUNT(CASE WHEN confirmed = -1 THEN 1 END) as cancelled
                FROM bookings 
                GROUP BY course_stream
                ORDER BY course_stream
            """)
            results = cursor.fetchall()
            return [dict(row) for row in results]
    finally:
        conn.close()

def get_all_bookings_with_stream():
    """Gets all bookings with course stream information for admin interface."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    b.id,
                    b.user_id,
                    b.username,
                    b.first_name,
                    b.course_id,
                    c.name as course_name,
                    b.confirmed,
                    b.course_stream,
                    b.created_at,
                    b.referral_code,
                    b.discount_percent
                FROM bookings b
                JOIN courses c ON b.course_id = c.id
                ORDER BY b.created_at DESC
            """)
            results = cursor.fetchall()
            return [dict(row) for row in results]
    finally:
        conn.close()