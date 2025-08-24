# db/base.py
import logging
import psycopg2
from psycopg2.extras import DictCursor
import config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logger.critical(f"Could not connect to PostgreSQL database: {e}")
        raise

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    return cursor.fetchone() is not None

def run_migrations():
    """Run database migrations for lesson types and course streams."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            logger.info("Running database migrations...")
            
            # Add lesson_type column to free_lesson_registrations
            if not check_column_exists(cur, 'free_lesson_registrations', 'lesson_type'):
                logger.info("Adding lesson_type column to free_lesson_registrations...")
                cur.execute("""
                    ALTER TABLE free_lesson_registrations 
                    ADD COLUMN lesson_type VARCHAR(50) DEFAULT 'cursor_lesson'
                """)
                
                # Update existing registrations to 'vibecoding_lesson'
                cur.execute("""
                    UPDATE free_lesson_registrations 
                    SET lesson_type = 'vibecoding_lesson' 
                    WHERE lesson_type = 'cursor_lesson'
                """)
                updated_count = cur.rowcount
                logger.info(f"Added lesson_type column and updated {updated_count} existing registrations to 'vibecoding_lesson'")
            
            # Add course_stream column to bookings
            if not check_column_exists(cur, 'bookings', 'course_stream'):
                logger.info("Adding course_stream column to bookings...")
                cur.execute("""
                    ALTER TABLE bookings 
                    ADD COLUMN course_stream VARCHAR(50) DEFAULT '4th_stream'
                """)
                
                # Update existing bookings to '3rd_stream'
                cur.execute("""
                    UPDATE bookings 
                    SET course_stream = '3rd_stream' 
                    WHERE course_stream = '4th_stream'
                """)
                updated_bookings = cur.rowcount
                logger.info(f"Added course_stream column and updated {updated_bookings} existing bookings to '3rd_stream'")
            
            # Migration: Change UNIQUE constraint from user_id to (user_id, lesson_type)
            cur.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'free_lesson_registrations' 
                AND constraint_type = 'UNIQUE'
                AND constraint_name LIKE '%user_id%'
            """)
            old_constraint = cur.fetchone()
            
            if old_constraint:
                logger.info(f"Removing old UNIQUE constraint on user_id: {old_constraint['constraint_name']}")
                cur.execute(f"""
                    ALTER TABLE free_lesson_registrations 
                    DROP CONSTRAINT {old_constraint['constraint_name']}
                """)
                logger.info("Old UNIQUE constraint removed")
            
            # Check if new composite constraint exists
            cur.execute("""
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'free_lesson_registrations_user_id_lesson_type_key'
            """)
            
            if not cur.fetchone():
                logger.info("Adding composite UNIQUE constraint (user_id, lesson_type)")
                cur.execute("""
                    ALTER TABLE free_lesson_registrations 
                    ADD CONSTRAINT free_lesson_registrations_user_id_lesson_type_key 
                    UNIQUE (user_id, lesson_type)
                """)
                logger.info("Composite UNIQUE constraint added successfully")
            
        conn.commit()
        logger.info("Database migrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during migrations: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def setup_database():
    """Ensures all required tables exist in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Таблица бронирований
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
                    discount_percent INTEGER DEFAULT 0,
                    course_stream VARCHAR(50) DEFAULT '4th_stream'
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

            # 6. Таблица регистраций на бесплатный урок
            cur.execute("""
                CREATE TABLE IF NOT EXISTS free_lesson_registrations (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    email TEXT NOT NULL,
                    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    notification_sent BOOLEAN DEFAULT FALSE,
                    lesson_type VARCHAR(50) DEFAULT 'cursor_lesson',
                    UNIQUE(user_id, lesson_type)
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
    
    # Run migrations after table setup
    run_migrations()