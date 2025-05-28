# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot for "HashSlash School" that handles course bookings and payment processing. The bot offers programming courses and consultations with integrated payment verification and admin moderation.

## Commands

- **Run the bot**: `python bot.py` or `./run.sh`
- **Install dependencies**: `pip install -r requirements.txt`
- **Setup configuration**: Copy `config.py.example` to `config.py` and fill in required values

## Architecture

### Core Components

1. **bot.py** - Main application with async handlers using python-telegram-bot v20+
   - ConversationHandler for managing multi-step booking flow
   - PicklePersistence for state management across restarts
   - Inline keyboards for interactive navigation

2. **Database** - SQLite with automatic schema migration
   - Extended bookings table tracking course_id, status, and timestamps
   - Unique constraints on (user_id, chosen_course, created_at)
   - Status codes: 0=pending, 1=payment_uploaded, 2=approved, -1=cancelled

3. **Payment Flow**
   - Multi-currency support with automatic exchange rate calculations
   - Photo upload for payment receipts
   - Admin notification system with approve/reject inline buttons
   - Different confirmation flows for courses vs consultations

### Key Technical Decisions

- Uses async/await patterns throughout for efficient handling
- Implements MarkdownV2 escaping for safe message formatting
- Separate logging for course selections (course_selections.log)
- 1-hour preliminary reservation system for bookings
- Comprehensive error handling with detailed logging

### Configuration Structure

The `config.py` file contains:
- BOT_TOKEN - Telegram bot API token
- ADMIN_CONTACT - Admin contact for support
- TARGET_CHAT_ID - Chat ID for admin notifications
- Payment details for multiple currencies (RUB, KZT, ARS, USDT)

### Important Patterns

When modifying the bot:
- All handlers should be async functions
- Use escape_markdown_v2() for any user-provided text
- Check booking status before allowing state transitions
- Log all critical actions and errors
- Maintain the conversation flow states (CHOOSING_COURSE, CONFIRMING_COURSE, etc.)