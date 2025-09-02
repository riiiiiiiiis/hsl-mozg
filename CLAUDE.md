# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot for "HashSlash School" that handles course bookings and payment processing. The bot offers AI-powered programming courses with integrated payment verification, referral system, and admin moderation.

## Commands

**Local Development Setup:**
```bash
# Setup and activation
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or venv\Scripts\activate on Windows

# Install dependencies (Python 3.11+ required)  
pip install -r requirements.txt

# Local database setup
docker-compose up -d

# Run the bot
python bot.py
```

**Quick Start (Alternative):**
```bash
git clone https://github.com/riiiiiiiiis/hsl-mozg.git
cd hsl-mozg
pip install -r requirements.txt
python bot.py
```

**Debugging and Testing:**
- **Test database connection**: `python -c "from db.base import test_connection; test_connection()"`
- **Check bot token**: Verify `BOT_TOKEN` is set in environment
- **Local PostgreSQL access**: Connection available on `localhost:5432` with credentials from docker-compose.yml
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
  - Scheduled datetime in ISO format with timezone (e.g., "2025-09-04T21:00:00+03:00")
  - Custom reminder_text for notifications
  - is_active flag to enable/disable lessons
- **Automatic filtering**: Lessons are automatically hidden after their time + 2-hour grace period
- **Database structure**: `free_lesson_registrations` table with `lesson_type` field
- **Registration flow**: 
  - Users can register for multiple different lesson types
  - Registration blocked for lessons that have passed their grace period
  - Shows "workshop already passed" message for expired lessons
  - **Repeating workshops supported**: Same lesson_type with different dates creates separate registrations
  - Database separates participants by `lesson_type` AND `lesson_date` for analytics
- **Notification system**: 
  - Automated reminders sent 15 minutes before each lesson
  - Notifications scheduled on bot startup using `asyncio.create_task()` 
  - Only sends to users who haven't received notifications yet (`notification_sent` flag)
  - Creates inline keyboard button if `meeting_url` field exists in lesson data
  - Uses `utils/notifications.py` for scheduling and delivery
  - Logs successful/failed deliveries and marks notifications as sent
  - Events logged: `free_lesson_reminder_sent`, `lesson_link_clicked`
- **Callback handlers** in `handlers/callback_handlers.py`:
  - `CALLBACK_LESSON_LINK_PREFIX` ("lesson_link_") for meeting URL buttons  
  - `handle_lesson_link_click()` processes button clicks and sends meeting links
  - Button clicks logged as `lesson_link_clicked` events for analytics
  - Sends separate HTML message with clickable Google Meet link
- **Helper functions** in `utils/lessons.py`:
  - `get_lesson_by_id(id)` - returns lesson_type and lesson_data
  - `get_active_lessons()` - returns only active lessons that haven't passed (considers 2-hour grace period)
  - `get_lesson_by_type(lesson_type)` - returns lesson_data by lesson_type
  - `reload_lessons()` - clears cache and reloads from YAML
- **Admin functions**: 
  - View registration stats by lesson type
  - Test notifications for specific lessons (`send_test_notification()`)
  - Monitor notification scheduling status (`get_notification_status()`)
  - Check time until lesson starts (`get_time_until_lesson()`)

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

**Required Environment Variables** (set in `.env` file or system):
```env
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql://user:pass@host:port/db
TARGET_CHAT_ID=admin_chat_id
ADMIN_CONTACT=@your_admin_contact
```

**Payment Configuration:**
```env
# Russian Ruble payments
TBANK_CARD_NUMBER=1234 5678 9012 3456
TBANK_CARD_HOLDER=Name Surname

# Kazakhstani Tenge payments  
KASPI_CARD_NUMBER=1234 5678 9012 3456

# Argentine Peso payments
ARS_ALIAS=your.alias

# USDT payments
USDT_TRC20_ADDRESS=your_address
BINANCE_ID=123456789
CRYPTO_NETWORK=TRC-20
```

**Exchange Rates:**
```env
USD_TO_RUB_RATE=95.0
USD_TO_KZT_RATE=470.0  
USD_TO_ARS_RATE=1000.0
```

**Referral System:** `REFERRAL_*` variables for bot URL, parameters, discount settings

**Local Development:** Docker-compose provides PostgreSQL on `localhost:5432` with credentials:
- User: `botuser` 
- Password: `botpassword`
- Database: `botdb`

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
  - Use ISO datetime format with timezone: "2025-09-04T21:00:00+03:00"
  - Set `is_active: false` to manually disable a lesson
  - Lessons automatically hide 2 hours after their scheduled time
  - Helper functions in `utils/lessons.py` handle loading, caching, and time filtering
  - **For repeating workshops**: Simply update the datetime - database will separate registrations by date automatically

- **Text message changes**:
  - Edit user-facing texts in `locales/ru.py`
  - Use `get_text(category, key, **kwargs)` function for formatted texts

- **Meeting URL handling**:
  - **CRITICAL**: Meeting URLs for lessons MUST NEVER appear in reminder text messages
  - Meeting URLs should ONLY be accessible through inline keyboard buttons
  - Add `meeting_url` field to lesson data in `data/lessons.yaml` to enable the button
  - Inline button "🔗 Присоединиться к уроку" appears automatically when `meeting_url` is present
  - Button click triggers callback handler that sends separate message with clickable link
  - `reminder_text` should end with friendly message like "Увидимся на уроке! 👋" (no URLs)

### Technology Stack

- **Python**: 3.11+ required
- **Dependencies** (from requirements.txt):
  - `python-telegram-bot[job-queue]>=20.0` - Telegram Bot API 
  - `psycopg2-binary` - PostgreSQL adapter
  - `python-dotenv` - Environment variable management
  - `PyYAML>=6.0` - YAML file parsing
- **Database**: PostgreSQL 14+
- **Deployment**: Railway with GitHub auto-deploy
- **Architecture**: Async/await throughout with polling mode (no webhooks)

### Content Management

The bot separates content from code using YAML files:

**Course Management (data/courses.yaml):**
```yaml
courses:
  - id: 1
    name: "Вайб кодинг"
    button_text: "Полный курс" 
    description: "AI-powered programming course..."
    price_usd: 150
    is_active: true
    start_date_text: "1 сентября"
```

**Free Lessons (data/lessons.yaml):**
```yaml
lessons:
  cursor_lesson:
    id: 1
    title: "Урок по Cursor"
    button_text: "🆓 Бесплатный урок"
    description: "Learn Cursor AI coding assistant..."
    datetime: "2025-09-02T21:00:00+03:00"  # ISO format with timezone
    is_active: true
    meeting_url: "https://meet.google.com/abc-defg-hij"
    reminder_text: |
      ⏰ Урок начинается через 15 минут!
      
      {description}
      
      Увидимся на уроке! 👋
```

**User Messages (locales/ru.py):**
```python
def get_text(category, key, **kwargs):
    # Centralized text management with formatting
```

### Testing & Debugging

- **Testing notification system**:
  ```python
  from utils.notifications import send_test_notification, get_notification_status
  from telegram.ext import Application
  
  # Send test notification to specific user
  await send_test_notification(application, "vibecoding_lesson", user_id=123456)
  
  # Check notification scheduling status for all lessons
  status = get_notification_status()
  print(status)
  ```

- **Testing lesson link buttons**:
  1. Register for a lesson that has `meeting_url` field
  2. Trigger test notification manually
  3. Click the "🔗 Присоединиться к уроку" button
  4. Verify you get separate message with clickable Google Meet link
  5. Check logs for `lesson_link_clicked` event

- **Checking event logs**:
  ```python
  from db.events import get_recent_events
  
  # Check recent lesson-related events
  events = get_recent_events(limit=100)
  lesson_events = [e for e in events if 'lesson' in e['action']]
  
  # Check specific event types
  reminder_events = [e for e in events if e['action'] == 'free_lesson_reminder_sent']
  click_events = [e for e in events if e['action'] == 'lesson_link_clicked']
  ```

- **Common debugging scenarios**:
  - **No notification button**: Check if `meeting_url` field exists in lesson YAML
  - **Button not working**: Check `CALLBACK_LESSON_LINK_PREFIX` handler in callback_handlers.py
  - **Wrong meeting link**: Verify `meeting_url` field value in lessons.yaml
  - **Notification not sent**: Check bot startup logs for scheduling errors
  - **Time zone issues**: Verify lesson `datetime` uses proper timezone format

### Deployment

**⚠️ CRITICAL DEPLOYMENT RULES:**
- **NEVER USE CLI DEPLOYMENT** - This crashes the database and can cause data loss
- **ONLY DEPLOY VIA GITHUB** - Push to repository and let Railway auto-deploy
- **NEVER use `mcp__railway-mcp-server__deploy`** - This CLI command is FORBIDDEN
- **Always commit changes first** before any deployment
- **Test locally** before pushing to GitHub

**Deployment Process:**
1. Test changes locally with `python bot.py`
2. Commit changes: `git add -A && git commit -m "message"`
3. Push to GitHub: `git push origin main`
4. Railway auto-deploys from GitHub webhook
5. Monitor deployment in Railway dashboard

**Railway Setup:**
- Uses Procfile with worker dyno type
- Auto-deploy from GitHub main branch
- Database migrations run automatically on startup
- PyYAML dependency automatically installed via requirements.txt

**Free lesson notifications**: 
- Automatically scheduled for all active lessons on bot startup
- No immediate notifications sent on deployment
- Uses precise timing based on lesson datetime minus 15 minutes
- Logs all scheduling activities for monitoring

## Railway Deployment Notes

### Known Issues with Railway Tools

**Railway MCP Timeout Issue**: 
- **NEVER USE**: `mcp__railway-mcp-server__get-logs` - this command ALWAYS hangs/timeouts
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

### Key Bot Commands

**User Commands:**
- `/start` - Main menu with course/lesson options
- `/start ref_CODE` - Activate referral code during registration
- `/reset` - Clear user session data

**Admin Commands:**
- `/create_referral [percent] [max_uses]` - Generate discount coupon
- `/referral_stats` - View referral usage statistics  
- `/stats` - Overall bot usage analytics

### Main User Flows

**Course Booking Process:**
1. User selects course → Shows price in multiple currencies
2. Referral code validation (if provided) → Apply discount
3. 1-hour booking hold created → Payment instructions sent
4. User uploads payment receipt → Admin gets approval buttons
5. Admin approves/rejects → User gets confirmation/refund instructions
6. Event logging for analytics throughout process

**Free Lesson Registration:**
1. User selects lesson → Email input required
2. Registration saved → Confirmation sent
3. Automated reminder 15 minutes before lesson
4. Meeting link delivered via inline button (URLs never in text messages)

### Data Architecture

**Core Tables:**
- `bookings` - Course purchases with referral tracking
- `free_lesson_registrations` - Lesson signups with email collection
- `referral_coupons` & `referral_usage` - Discount system
- `events` - Analytics and user interaction tracking

**Content Separation:**
- Course data: `data/courses.yaml` → Database sync on startup
- Lesson data: `data/lessons.yaml` → Cached with auto-expiration
- UI text: `locales/ru.py` → Centralized messaging system
- Meeting URLs: Secured through inline buttons only