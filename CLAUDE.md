# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot for "HashSlash School" that handles course bookings and payment processing. The bot offers AI-powered programming courses with integrated payment verification, referral system, and admin moderation.

## Commands

- **Setup virtual environment**: 
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # On macOS/Linux
  # or
  venv\Scripts\activate  # On Windows
  ```
- **Install dependencies**: `pip install -r requirements.txt` (Python 3.11+ required)
- **Run the bot**: `source venv/bin/activate && python bot.py`
- **Setup database**: `docker-compose up -d` for local PostgreSQL
- **Test database connection**: `source venv/bin/activate && python -c "from db.base import test_connection; test_connection()"`
- **Configuration**: Create `.env` file with required variables (see Configuration Structure below)

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
  - Scheduled datetime in ISO format with timezone (e.g., "2025-08-25T21:00:00+03:00")
  - Custom reminder_text for notifications
  - is_active flag to enable/disable lessons
- **Automatic filtering**: Lessons are automatically hidden after their time + 2-hour grace period
- **Database structure**: `free_lesson_registrations` table with `lesson_type` field
- **Registration flow**: 
  - Users can register for multiple different lesson types
  - Registration blocked for lessons that have passed their grace period
  - Shows "workshop already passed" message for expired lessons
- **Notification system**: Automated reminders sent 15 minutes before each lesson
- **Helper functions** in `utils/lessons.py`:
  - `get_lesson_by_id(id)` - returns lesson_type and lesson_data
  - `get_active_lessons()` - returns only active lessons that haven't passed (considers 2-hour grace period)
  - `get_lesson_by_type(lesson_type)` - returns lesson_data by lesson_type
  - `reload_lessons()` - clears cache and reloads from YAML
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
- Timezone-aware datetime handling for lessons (UTC internally, display in local time)
- Automatic lesson expiration with configurable grace period

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
  - Use ISO datetime format with timezone: "2025-09-02T21:00:00+03:00"
  - Set `is_active: false` to manually disable a lesson
  - Lessons automatically hide 2 hours after their scheduled time
  - Helper functions in `utils/lessons.py` handle loading, caching, and time filtering

- **Text message changes**:
  - Edit user-facing texts in `locales/ru.py`
  - Use `get_text(category, key, **kwargs)` function for formatted texts

### Common Development Tasks

- **Adding new free lessons**:
  ```yaml
  # In data/lessons.yaml
  new_lesson:
    id: 4  # Unique ID
    title: "New Workshop"
    button_text: "Register for Workshop"
    description: "Full description..."
    datetime: "2025-09-10T19:00:00+03:00"  # With timezone
    is_active: true
    reminder_text: "Workshop starts in 15 minutes!"
  ```
  Then reload cache: `from utils.lessons import reload_lessons; reload_lessons()`

- **Testing payment flow locally**:
  1. Start bot with test credentials
  2. Send `/start` to initiate booking
  3. Upload any image as payment receipt
  4. Check admin chat for approval buttons
  5. Click approve to complete flow

- **Checking event logs**:
  ```python
  from db.events import get_recent_events
  events = get_recent_events(limit=50)
  ```

- **Managing lesson visibility**:
  - Set `is_active: false` to hide immediately
  - Lessons auto-hide 2 hours after `datetime`
  - Check active lessons: `from utils.lessons import get_active_lessons`

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

## Railway Deployment Notes

### Known Issues with Railway Tools

**Railway MCP Timeout Issue**: 
- Railway MCP commands (especially `get-logs`) may hang/timeout due to large log volume
- The bot generates continuous polling logs (Telegram getUpdates every 10 seconds)
- **Solution**: Use direct Railway CLI commands instead of Railway MCP when possible:
  ```bash
  railway status                    # Check project status
  railway logs --service worker     # Get logs (may timeout with large volumes)
  railway whoami                    # Check authentication
  ```

**Log Volume Management**:
- Worker service generates ~6 log entries per minute (continuous Telegram polling)
- Logs include HTTP requests to Telegram API every 10 seconds
- For troubleshooting, use `railway logs --tail 50` to limit output
- Consider log rotation or filtering for production monitoring

### Database Access
- Use Railway MCP `list-variables` to get DATABASE_PUBLIC_URL
- Connect via psql: `psql "postgresql://user:pass@host:port/db"`
- Database credentials available through Railway variables (service: Postgres)
- Railway-db Claude Code agent available for database operations