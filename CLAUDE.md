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
- **Run tests**: No test framework currently configured

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
   - **db/courses.py**: Course catalog operations (now reads from constants.py instead of database)
   - **db/course_validation.py**: Validates course data structure and ensures data integrity
   - **db/events.py**: Event logging and analytics
   - **db/referrals.py**: Referral coupon system
   - Tables: bookings, referral_coupons, referral_usage, events (courses table no longer used)

3. **Handlers** - Modular command and callback handling
   - **handlers/command_handlers.py**: `/start`, `/reset`, `/stats`, `/create_referral`, `/referral_stats`
   - **handlers/callback_handlers.py**: Inline keyboard interactions
   - **handlers/message_handlers.py**: Photo upload for payment receipts

4. **Payment Flow**
   - Multi-currency support with automatic exchange rate calculations
   - Photo upload for payment receipts
   - Admin notification system with approve/reject inline buttons
   - Referral discount system (10-100% off)
   - Event tracking for analytics

5. **Admin Tools**
   - Currently no admin interface in codebase
   - Admin functions via Telegram commands only
   - Stats available through `/stats` command

### Course Structure

- Courses stored in constants.py (hardcoded for easier content management):
  - "Вайб Кодинг CORE" ($100, ID: 1)
  - "Вайб Кодинг EXTRA" ($200, ID: 2)
- Both courses start July 23rd
- Focus: AI-assisted coding without prior experience
- Course data structure includes:
  - Required fields: id, name, button_text, description, price_usd
  - Optional fields: price_usd_cents, is_active, start_date_text
  - Automatic validation on first access via db/course_validation.py
  - Validation includes type checking, required field presence, and data consistency

### Key Technical Decisions

- Uses async/await patterns throughout for efficient handling
- PostgreSQL database with connection pooling
- Modular architecture with separate handler and database modules
- Event-driven analytics system for tracking user actions
- Referral system with flexible discount coupons
- Comprehensive error handling with detailed logging
- Admin notifications use HTML parse mode for better formatting
- No webhook usage - polling mode only

### Configuration Structure

Environment variables (set in `.env` file or system):
- `DATABASE_URL` - PostgreSQL connection string
- `BOT_TOKEN` - Telegram bot API token
- `TARGET_CHAT_ID` - Chat ID for admin notifications
- `ADMIN_CONTACT` - Admin contact for support
- Payment details for multiple currencies:
  - `RUB_*` - Russian Ruble payment details
  - `KZT_*` - Kazakhstani Tenge payment details
  - `ARS_*` - Argentine Peso payment details
  - `USDT_*` - USDT (Tether) payment details
- Exchange rates: `KZT_TO_USD`, `RUB_TO_USD`, `ARS_TO_USD`

### Important Patterns

When modifying the bot:
- All handlers should be async functions
- Use escape_markdown_v2() for any user-provided text
- Database operations use connection pooling - don't manually manage connections
- Event logging for analytics: log_event(user_id, action, details)
- Referral validation happens during course selection
- Always handle photo uploads as list (update.message.photo[-1])
- Use constants.py for static values and course definitions
- Course data changes:
  - Edit course information directly in constants.py COURSES list
  - Ensure all required fields are present (validation will catch errors)
  - Run tests after changes: `python3 test_courses.py`
  - Course data is validated on first access and cached for performance

### Deployment

- **Heroku**: Uses Procfile with web dyno type
- **Local**: docker-compose.yml for PostgreSQL setup
- Auto-updates course data on bot startup
- No CI/CD pipeline configured