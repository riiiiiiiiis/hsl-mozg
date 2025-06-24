# db/referrals.py
import random
import string
import logging
import psycopg2
from psycopg2.extras import DictCursor
from db.base import get_db_connection
import constants

logger = logging.getLogger(__name__)

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