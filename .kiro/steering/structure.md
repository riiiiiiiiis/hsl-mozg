# Project Structure

## Root Level
- `bot.py` - Main bot entry point with handler registration
- `config.py` - Configuration management (create from config.py.example)
- `constants.py` - Application constants and static data
- `utils.py` - Shared utility functions
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment configuration
- `docker-compose.yml` - Local PostgreSQL setup

## Core Modules

### `/handlers/` - Telegram Bot Handlers
- `command_handlers.py` - Command handlers (/start, /reset, /stats, etc.)
- `callback_handlers.py` - Inline button callback handlers
- `message_handlers.py` - Message handlers (photo uploads, text)

### `/db/` - Database Layer
- `base.py` - Database connection and table setup
- `courses.py` - Course management operations
- `bookings.py` - Booking CRUD operations
- `referrals.py` - Referral system database operations
- `events.py` - Event logging and statistics

### `/db_management/` - Database Utilities
- `populate_initial_course.py` - Course data initialization

## Architecture Patterns

### Handler Pattern
- Separate handlers for commands, callbacks, and messages
- Main callback handler acts as router for different callback types
- Each handler focuses on single responsibility

### Database Layer
- Dedicated modules for each data domain
- Connection management centralized in `base.py`
- Auto-migration on startup

### Configuration Management
- Environment variable based configuration
- Template file (`config.py.example`) for setup
- Sensitive data excluded from version control

## File Naming Conventions
- Snake_case for Python files and functions
- Descriptive module names reflecting functionality
- Database modules match table/domain names
- Handler modules grouped by Telegram API handler type

## Import Structure
- Relative imports within packages
- Constants imported at module level
- Database modules imported as needed
- Configuration imported globally where needed