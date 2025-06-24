# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot for "HashSlash School" that handles course bookings and payment processing. The bot offers programming courses and consultations with integrated payment verification and admin moderation.

## Commands

- **Run the bot**: `python bot.py` or `./run.sh`
- **Install dependencies**: `pip install -r requirements.txt`
- **Setup configuration**: Copy `config.py.example` to `config.py` and fill in required values
- **Run web admin**: `python web_admin.py` or `./start_web_admin.sh`
- **Run desktop admin**: `python admin_panel.py` or double-click `start_admin_panel.command`
- **Run tests**: No test framework currently configured

## Architecture

### Core Components

1. **bot.py** - Main application with async handlers using python-telegram-bot v20+
   - ConversationHandler for managing multi-step booking flow
   - PicklePersistence for state management across restarts (conversation_state.pickle)
   - Inline keyboards for interactive navigation
   - States: CHOOSING_COURSE → CONFIRMING_COURSE → AWAITING_PAYMENT → PAYMENT_UPLOADED

2. **Database** - SQLite with automatic schema migration
   - Extended bookings table: `id, user_id, username, first_name, chosen_course, course_id, confirmed, created_at`
   - Unique constraints on (user_id, chosen_course, created_at)
   - Status codes: 0=pending, 1=payment_uploaded, 2=approved, -1=cancelled
   - Note: bookings.sql is outdated - bot.py contains actual schema

3. **Payment Flow**
   - Multi-currency support with automatic exchange rate calculations
   - Photo upload for payment receipts
   - Admin notification system with approve/reject inline buttons
   - Different confirmation flows for courses vs consultations
   - 1-hour preliminary reservation system

4. **Admin Tools**
   - **web_admin.py**: Flask-based web interface (port 5000)
     - Dashboard with statistics
     - User management (confirmed/unconfirmed lists)
     - Bulk messaging to confirmed users
   - **admin_panel.py**: Tkinter desktop GUI
     - View confirmed/unconfirmed users
     - Statistics display
   - **Utility scripts**: Individual task-specific scripts

### Course Structure

- Courses defined in bot.py: 
  - "Вайб Кодинг" ($70)
  - "Консультация по Blockchain" ($25)
  - "Консультация ChatGPT" ($25)
- Consultations receive calendar link after approval
- Courses receive general confirmation

### Key Technical Decisions

- Uses async/await patterns throughout for efficient handling
- Implements MarkdownV2 escaping for safe message formatting
- Separate logging for course selections (course_selections.log)
- Webhook deletion on startup to prevent conflicts
- Comprehensive error handling with detailed logging
- Admin notifications use HTML parse mode for better formatting

### Configuration Structure

The `config.py` file contains:
- BOT_TOKEN - Telegram bot API token
- ADMIN_CONTACT - Admin contact for support  
- TARGET_CHAT_ID - Chat ID for admin notifications
- Payment details for multiple currencies (RUB, KZT, ARS, USDT)
- Exchange rates for currency conversions

### Important Patterns

When modifying the bot:
- All handlers should be async functions
- Use escape_markdown_v2() for any user-provided text
- Check booking status before allowing state transitions
- Log all critical actions and errors
- Maintain the conversation flow states
- Use transaction management for database operations
- Always handle photo uploads as list (update.message.photo[-1])