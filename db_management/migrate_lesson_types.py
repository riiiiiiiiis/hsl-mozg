#!/usr/bin/env python3
"""
Migration script to add lesson_type column to free_lesson_registrations table
and course_stream column to bookings table.

This script:
1. Adds lesson_type column to free_lesson_registrations with default 'cursor_lesson'
2. Adds course_stream column to bookings with default '4th_stream'
3. Updates existing free lesson registrations to 'vibecoding_lesson'
4. Provides rollback functionality
"""

import logging
import psycopg2
from psycopg2.extras import DictCursor
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

def migrate_forward():
    """Apply the migration - add new columns and update existing data."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            logger.info("Starting forward migration...")
            
            # 1. Add lesson_type column to free_lesson_registrations
            if not check_column_exists(cur, 'free_lesson_registrations', 'lesson_type'):
                logger.info("Adding lesson_type column to free_lesson_registrations...")
                cur.execute("""
                    ALTER TABLE free_lesson_registrations 
                    ADD COLUMN lesson_type VARCHAR(50) DEFAULT 'cursor_lesson'
                """)
                logger.info("lesson_type column added successfully")
            else:
                logger.info("lesson_type column already exists, skipping...")
            
            # 2. Add course_stream column to bookings
            if not check_column_exists(cur, 'bookings', 'course_stream'):
                logger.info("Adding course_stream column to bookings...")
                cur.execute("""
                    ALTER TABLE bookings 
                    ADD COLUMN course_stream VARCHAR(50) DEFAULT '4th_stream'
                """)
                logger.info("course_stream column added successfully")
            else:
                logger.info("course_stream column already exists, skipping...")
            
            # 3. Update existing free lesson registrations to 'vibecoding_lesson'
            logger.info("Updating existing free lesson registrations...")
            cur.execute("""
                UPDATE free_lesson_registrations 
                SET lesson_type = 'vibecoding_lesson' 
                WHERE lesson_type = 'cursor_lesson'
            """)
            updated_count = cur.rowcount
            logger.info(f"Updated {updated_count} existing registrations to 'vibecoding_lesson'")
            
            # 4. Update existing bookings to '3rd_stream' (previous stream)
            logger.info("Updating existing bookings...")
            cur.execute("""
                UPDATE bookings 
                SET course_stream = '3rd_stream' 
                WHERE course_stream = '4th_stream'
            """)
            updated_bookings = cur.rowcount
            logger.info(f"Updated {updated_bookings} existing bookings to '3rd_stream'")
            
        conn.commit()
        logger.info("Forward migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during forward migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_rollback():
    """Rollback the migration - remove added columns."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            logger.info("Starting rollback migration...")
            
            # Remove lesson_type column from free_lesson_registrations
            if check_column_exists(cur, 'free_lesson_registrations', 'lesson_type'):
                logger.info("Removing lesson_type column from free_lesson_registrations...")
                cur.execute("ALTER TABLE free_lesson_registrations DROP COLUMN lesson_type")
                logger.info("lesson_type column removed successfully")
            else:
                logger.info("lesson_type column doesn't exist, skipping...")
            
            # Remove course_stream column from bookings
            if check_column_exists(cur, 'bookings', 'course_stream'):
                logger.info("Removing course_stream column from bookings...")
                cur.execute("ALTER TABLE bookings DROP COLUMN course_stream")
                logger.info("course_stream column removed successfully")
            else:
                logger.info("course_stream column doesn't exist, skipping...")
            
        conn.commit()
        logger.info("Rollback migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during rollback migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_migration_status():
    """Check current migration status."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            lesson_type_exists = check_column_exists(cur, 'free_lesson_registrations', 'lesson_type')
            course_stream_exists = check_column_exists(cur, 'bookings', 'course_stream')
            
            logger.info(f"Migration status:")
            logger.info(f"  lesson_type column exists: {lesson_type_exists}")
            logger.info(f"  course_stream column exists: {course_stream_exists}")
            
            if lesson_type_exists:
                cur.execute("SELECT lesson_type, COUNT(*) FROM free_lesson_registrations GROUP BY lesson_type")
                lesson_stats = cur.fetchall()
                logger.info(f"  Free lesson registrations by type: {dict(lesson_stats)}")
            
            if course_stream_exists:
                cur.execute("SELECT course_stream, COUNT(*) FROM bookings GROUP BY course_stream")
                booking_stats = cur.fetchall()
                logger.info(f"  Bookings by stream: {dict(booking_stats)}")
                
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python migrate_lesson_types.py [forward|rollback|status]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "forward":
        migrate_forward()
    elif command == "rollback":
        migrate_rollback()
    elif command == "status":
        get_migration_status()
    else:
        print("Invalid command. Use 'forward', 'rollback', or 'status'")
        sys.exit(1)