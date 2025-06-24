import logging
import random
import string
import psycopg2
from psycopg2.extras import DictCursor

import config
import constants

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logger.critical(f"Could not connect to PostgreSQL database: {e}")
        raise

def setup_database():
    """Ensures all required tables exist in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    chosen_course TEXT,
                    course_id TEXT,
                    confirmed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    referral_code TEXT,
                    discount_percent INTEGER DEFAULT 0
                );
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {constants.REFERRAL_TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT,
                    discount_percent INTEGER NOT NULL,
                    max_activations INTEGER NOT NULL,
                    current_activations INTEGER DEFAULT 0,
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                );
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {constants.REFERRAL_USAGE_TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    coupon_id INTEGER NOT NULL,
                    user_id BIGINT NOT NULL,
                    booking_id INTEGER,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (coupon_id) REFERENCES {constants.REFERRAL_TABLE_NAME}(id),
                    FOREIGN KEY (booking_id) REFERENCES bookings(id),
                    UNIQUE(coupon_id, user_id)
                );
            """)
        conn.commit()
        logger.info("Database setup complete. Tables are verified.")
    except Exception as e:
        logger.error(f"Error during table creation/check in PostgreSQL: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def create_booking(user_id, username, first_name, course_name, course_id, referral_code, discount_percent):
    """Creates a new booking record and returns the new booking ID."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                """INSERT INTO bookings (user_id, username, first_name, chosen_course, course_id, confirmed, referral_code, discount_percent)
                   VALUES (%s, %s, %s, %s, %s, 0, %s, %s) RETURNING id""",
                (user_id, username, first_name, course_name, course_id, referral_code, discount_percent)
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
            cursor.execute(
                "SELECT id, chosen_course FROM bookings WHERE user_id = %s AND confirmed = 0 ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            return cursor.fetchone()
    finally:
        conn.close()

def update_booking_status(booking_id, status_code):
    """Updates the 'confirmed' status of a specific booking."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE bookings SET confirmed = %s WHERE id = %s", (status_code, booking_id))
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()

def get_booking_details(booking_id):
    """Retrieves details for a specific booking."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT chosen_course, course_id FROM bookings WHERE id = %s", (booking_id,))
            return cursor.fetchone()
    finally:
        conn.close()

# --- Referral System Functions ---

def generate_and_save_referral_code(discount, activations, creator_id):
    """Generates a unique referral code and saves it to the database."""
    while True:
        code = ''.join(random.choices(constants.REFERRAL_CODE_CHARS, k=constants.REFERRAL_CODE_LENGTH))
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT id FROM {constants.REFERRAL_TABLE_NAME} WHERE code = %s", (code,))
                if not cursor.fetchone():
                    cursor.execute(
                        f"""INSERT INTO {constants.REFERRAL_TABLE_NAME} (code, discount_percent, max_activations, created_by)
                            VALUES (%s, %s, %s, %s)""",
                        (code, discount, activations, creator_id)
                    )
                    conn.commit()
                    return code
        finally:
            conn.close()

def validate_referral_code(code, user_id):
    """Validates a referral code and returns its details if valid."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(f"""
                SELECT id, name, discount_percent, max_activations, current_activations
                FROM {constants.REFERRAL_TABLE_NAME}
                WHERE code = %s AND is_active = 1
            """, (code,))
            coupon = cursor.fetchone()
            if not coupon:
                return None, "not_found"
            if coupon['current_activations'] >= coupon['max_activations']:
                return None, "expired"
            return coupon, "valid"
    finally:
        conn.close()

def apply_referral_discount(coupon_id, user_id, booking_id):
    """Records the usage of a referral coupon."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {constants.REFERRAL_USAGE_TABLE_NAME} (coupon_id, user_id, booking_id)
                VALUES (%s, %s, %s)
            """, (coupon_id, user_id, booking_id))
            cursor.execute(f"""
                UPDATE {constants.REFERRAL_TABLE_NAME}
                SET current_activations = current_activations + 1
                WHERE id = %s
            """, (coupon_id,))
            conn.commit()
            return True
    except psycopg2.Error as e:
        logger.error(f"Error applying referral discount: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_referral_stats():
    """Retrieves statistics for the most recent referral coupons."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(f"""
                SELECT code, discount_percent, max_activations, current_activations, is_active
                FROM {constants.REFERRAL_TABLE_NAME}
                ORDER BY created_at DESC LIMIT 20
            """)
            return cursor.fetchall()
    finally:
        conn.close()