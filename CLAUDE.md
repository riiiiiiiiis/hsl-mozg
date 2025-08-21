# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot for "HashSlash School" that handles course bookings and payment processing. The bot offers AI-powered programming courses with integrated payment verification, referral system, and admin moderation.

## Commands

- **Run the bot**: `python bot.py` or `./run.sh`
- **Install dependencies**: `pip install -r requirements.txt` (includes PyYAML for data files)
- **Setup configuration**: Set environment variables (see Configuration Structure below)
- **Setup database**: `docker-compose up -d` for local PostgreSQL
- **Populate courses**: Courses are now loaded from `data/courses.yaml`

## Architecture

### Core Components

1. **bot.py** - Main entry point
   - Sets up bot application with handlers
   - Initializes database on startup
   - Auto-updates courses on deployment
   - Uses polling mode (not webhooks)

2. **Data Layer** - Separated content from code
   - **data/courses.yaml**: Course information in YAML format
   - **data/lessons.yaml**: Free lesson information in YAML format
   - **locales/ru.py**: All user-facing text messages
   - **utils/courses.py**: Helper functions for course operations
   - **utils/lessons.py**: Helper functions for lesson operations
   - **handlers/callbacks.py**: Callback constants and routing

3. **Database** - PostgreSQL with modular structure
   - **db/base.py**: Database connection and schema setup
   - **db/bookings.py**: Booking management with referral support
   - **db/courses.py**: Course catalog operations (reads from YAML files)
   - **db/course_validation.py**: Validates course data structure
   - **db/events.py**: Event logging and analytics
   - **db/referrals.py**: Referral coupon system
   - **db/free_lessons.py**: Free lesson registrations
   - Tables: bookings, referral_coupons, referral_usage, events, free_lesson_registrations

4. **Handlers** - Modular command and callback handling
   - **handlers/command_handlers.py**: `/start`, `/reset`, `/stats`, `/create_referral`, `/referral_stats`
   - **handlers/callback_handlers.py**: Inline keyboard interactions via main_callback_handler router
   - **handlers/message_handlers.py**: Photo upload for payment receipts and general messages

5. **Payment Flow**
   - Multi-currency support (RUB, KZT, ARS, USDT) with automatic exchange rate calculations
   - Photo upload for payment receipts
   - Admin notification system with approve/reject inline buttons
   - Referral discount system (10-100% off)
   - Event tracking for analytics

### Course Structure

- Courses stored in `data/courses.yaml` (YAML format for easy editing):
  - "Вайб кодинг" ($150, ID: 1)
- Course starts September 1st  
- Course data structure includes:
  - Required fields: id, name, button_text, description, price_usd
  - Optional fields: price_usd_cents, is_active, start_date_text
  - Automatic validation on first access via db/course_validation.py
- Helper functions in `utils/courses.py` for loading and accessing courses

### Free Lessons System

- **Multiple free lessons** stored in `data/lessons.yaml` (YAML format)
- Each free lesson has:
  - Unique ID for callback routing
  - lesson_type (key) for database operations
  - Full description including date, time, and links
  - Scheduled datetime in ISO format for automatic notifications
  - Custom reminder_text for notifications
- **Database structure**: `free_lesson_registrations` table with `lesson_type` field
- **Registration flow**: Users can register for multiple different lesson types
- **Notification system**: Automated reminders sent 15 minutes before each lesson
- **Helper functions** in `utils/lessons.py`:
  - `get_lesson_by_id(id)` - returns lesson_type and lesson_data
  - `get_active_lessons()` - returns dict of active lessons only  
  - `get_lesson_by_type(lesson_type)` - returns lesson_data by lesson_type
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
- Referral system configuration: `REFERRAL_*` variables for bot URL, parameters, discount settings

### Important Patterns

When modifying the bot:
- All handlers should be async functions
- Use escape_markdown_v2() for any user-provided text in messages
- Database operations use connection pooling - don't manually manage connections
- Event logging for analytics: log_event(user_id, action, details)
- Referral validation happens during course selection
- Always handle photo uploads as list (update.message.photo[-1])
- **Course data changes**:
  - Edit course information in `data/courses.yaml` 
  - Ensure all required fields are present (validation will catch errors)
  - Course data is validated on first access and cached for performance
  - Helper functions automatically load from YAML files

- **Free lesson changes**:
  - Edit lesson information in `data/lessons.yaml`
  - Use ISO datetime format: "2025-09-02T21:00:00"
  - Helper functions in `utils/lessons.py` handle loading and caching

- **Text message changes**:
  - Edit user-facing texts in `locales/ru.py`
  - Use `get_text(category, key, **kwargs)` function for formatted texts

### Free Lesson Management

- **Adding new free lessons**:
  - Add new entry to `data/lessons.yaml` with unique lesson_type key
  - Include: id, title, button_text, description (with full info), datetime (ISO format), is_active, reminder_text
  - The lesson_type key becomes the database identifier
  - Use `utils/lessons.py` functions to reload cached data: `reload_lessons()`
- **Notification system**:
  - Notifications scheduled automatically at bot startup for all active lessons
  - Sent exactly 15 minutes before lesson datetime
  - Uses `asyncio.create_task()` for precise timing
  - No force_send on deployment - only scheduled notifications
- **Database operations**:
  - Use lesson_type to filter registrations: `get_registrations_by_type(lesson_type)`
  - Mark notifications sent: `mark_notification_sent(registration_id)`
  - Check user registration: `is_user_registered_for_lesson_type(user_id, lesson_type)`

### Deployment

- **Railway**: Uses Procfile with worker dyno type
- **Local**: docker-compose.yml for PostgreSQL setup  
- Course and lesson data loaded from YAML files on bot startup
- Database migrations run automatically on startup
- PyYAML dependency automatically installed via requirements.txt
- **Free lesson notifications**: 
  - Automatically scheduled for all active lessons on bot startup
  - No immediate notifications sent on deployment
  - Uses precise timing based on lesson datetime minus 15 minutes
  - Logs all scheduling activities for monitoring
- запускай локально питон только внутри виртуального окружения