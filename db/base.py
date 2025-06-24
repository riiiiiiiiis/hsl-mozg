# db/base.py
import logging
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
            # 1. Таблица курсов
            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price_usd_cents INTEGER NOT NULL DEFAULT 0,
                    button_text VARCHAR(100) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    start_date_text VARCHAR(100)
                );
            """)

            # 2. Таблица бронирований
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    course_id INTEGER REFERENCES courses(id),
                    confirmed INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    referral_code TEXT,
                    discount_percent INTEGER DEFAULT 0
                );
            """)

            # 3. Таблица реферальных купонов
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {constants.REFERRAL_TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT,
                    discount_percent INTEGER NOT NULL,
                    max_activations INTEGER NOT NULL,
                    current_activations INTEGER DEFAULT 0,
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                );
            """)

            # 4. Таблица использования рефералов
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {constants.REFERRAL_USAGE_TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    coupon_id INTEGER NOT NULL REFERENCES {constants.REFERRAL_TABLE_NAME}(id),
                    user_id BIGINT NOT NULL,
                    booking_id INTEGER REFERENCES bookings(id),
                    used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(coupon_id, user_id)
                );
            """)

            # 5. Таблица событий для статистики
            cur.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    details JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

        conn.commit()
        logger.info("Database setup complete. All tables are verified.")
    except Exception as e:
        logger.error(f"Error during table creation/check: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()