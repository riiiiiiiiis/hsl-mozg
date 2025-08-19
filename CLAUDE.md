# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot for "HashSlash School" that handles course bookings and payment processing. The bot offers AI-powered programming courses with integrated payment verification, referral system, and admin moderation.

## Commands

- **Run the bot**: `python bot.py` or `./run.sh`
- **Install dependencies**: `pip install -r requirements.txt`
- **Setup configuration**: Copy `config.py.example` to `config.py` and set environment variables
- **Setup database**: `docker-compose up -d` for local PostgreSQL
- **Populate courses**: `python db_management/populate_initial_course.py`
- **Run tests**: `python test_courses.py` or other test files in root directory

## Architecture

### Core Components

1. **bot.py** - Main entry point
   - Sets up bot application with handlers
   - Initializes database on startup
   - Auto-updates courses on deployment
   - Uses polling mode (not webhooks)

2. **Database** - PostgreSQL with modular structure
   - **db/base.py**: Database connection and schema setup
   - **db/bookings.py**: Booking management with referral support
   - **db/courses.py**: Course catalog operations (reads from constants.py)
   - **db/course_validation.py**: Validates course data structure
   - **db/events.py**: Event logging and analytics
   - **db/referrals.py**: Referral coupon system
   - **db/free_lessons.py**: Free lesson registrations
   - Tables: bookings, referral_coupons, referral_usage, events, free_lesson_registrations

3. **Handlers** - Modular command and callback handling
   - **handlers/command_handlers.py**: `/start`, `/reset`, `/stats`, `/create_referral`, `/referral_stats`
   - **handlers/callback_handlers.py**: Inline keyboard interactions via main_callback_handler router
   - **handlers/message_handlers.py**: Photo upload for payment receipts and general messages

4. **Payment Flow**
   - Multi-currency support (RUB, KZT, ARS, USDT) with automatic exchange rate calculations
   - Photo upload for payment receipts
   - Admin notification system with approve/reject inline buttons
   - Referral discount system (10-100% off)
   - Event tracking for analytics

### Course Structure

- Course stored in constants.py (hardcoded for easier content management):
  - "Вайб кодинг" ($150, ID: 1)
- Course starts September 1st
- Course data structure includes:
  - Required fields: id, name, button_text, description, price_usd
  - Optional fields: price_usd_cents, is_active, start_date_text
  - Automatic validation on first access via db/course_validation.py

### Free Lessons System

- **Multiple free lessons** supported via `FREE_LESSONS` structure in constants.py
- Each free lesson has:
  - Unique ID for callback routing
  - lesson_type (key) for database operations
  - Full description including date, time, and links
  - Scheduled datetime for automatic notifications
  - Custom reminder_text for notifications
- **Database structure**: `free_lesson_registrations` table with `lesson_type` field
- **Registration flow**: Users can register for multiple different lesson types
- **Notification system**: Automated reminders sent 15 minutes before each lesson
- **Admin functions**: 
  - View registration stats by lesson type
  - Test notifications for specific lessons
  - Monitor notification scheduling status

### Key Technical Decisions

- Uses async/await patterns throughout for efficient handling
- PostgreSQL database with connection pooling via psycopg2
- Modular architecture with separate handler and database modules
- Event-driven analytics system for tracking user actions
- Referral system with flexible discount coupons
- Admin notifications use HTML parse mode for better formatting
- No webhook usage - polling mode only for simplicity

### Configuration Structure

Environment variables (set in `.env` file or system):
- `DATABASE_URL` - PostgreSQL connection string
- `BOT_TOKEN` - Telegram bot API token
- `TARGET_CHAT_ID` - Chat ID for admin notifications
- `ADMIN_CONTACT` - Admin contact for support
- Payment details for multiple currencies:
  - `TBANK_*` - Russian Ruble payment details
  - `KASPI_*` - Kazakhstani Tenge payment details
  - `ARS_*` - Argentine Peso payment details
  - `USDT_*` - USDT (Tether) payment details
- Exchange rates: `USD_TO_KZT_RATE`, `USD_TO_RUB_RATE`, `USD_TO_ARS_RATE`

### Important Patterns

When modifying the bot:
- All handlers should be async functions
- Use escape_markdown_v2() for any user-provided text in messages
- Database operations use connection pooling - don't manually manage connections
- Event logging for analytics: log_event(user_id, action, details)
- Referral validation happens during course selection
- Always handle photo uploads as list (update.message.photo[-1])
- Use constants.py for static values and course definitions
- Course data changes:
  - Edit course information directly in constants.py COURSES list
  - Ensure all required fields are present (validation will catch errors)
  - Run tests after changes: `python test_courses.py`
  - Course data is validated on first access and cached for performance

### Free Lesson Management

- **Adding new free lessons**:
  - Add new entry to `FREE_LESSONS` dict in constants.py with unique ID and lesson_type key
  - Include: id, title, button_text, description (with full info), datetime, is_active, reminder_text
  - The lesson_type key becomes the database identifier
- **Notification system**:
  - Notifications scheduled automatically at bot startup for all active lessons
  - Sent exactly 15 minutes before lesson datetime
  - Uses `asyncio.create_task()` for precise timing
  - No force_send on deployment - only scheduled notifications
- **Database operations**:
  - Use lesson_type to filter registrations: `get_registrations_by_type(lesson_type)`
  - Mark notifications sent: `mark_notification_sent(registration_id)`
  - Check user registration: `is_user_registered_for_lesson_type(user_id, lesson_type)`
- **Helper functions** available in constants.py:
  - `get_lesson_by_id(id)` - returns lesson_type and lesson_data
  - `get_active_lessons()` - returns dict of active lessons only  
  - `get_lesson_by_type(lesson_type)` - returns lesson_data by lesson_type

### Deployment

- **Railway**: Uses Procfile with worker dyno type
- **Local**: docker-compose.yml for PostgreSQL setup
- Auto-updates course data on bot startup via db_management/populate_initial_course.py
- Database migrations run automatically on startup
- **Free lesson notifications**: 
  - Automatically scheduled for all active lessons on bot startup
  - No immediate notifications sent on deployment
  - Uses precise timing based on lesson datetime minus 15 minutes
  - Logs all scheduling activities for monitoring