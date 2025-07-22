# Technology Stack

## Core Technologies
- **Python 3.11+** - Main programming language
- **python-telegram-bot v20+** - Asynchronous Telegram Bot API
- **PostgreSQL** - Primary database with psycopg2-binary driver
- **Flask** - Web admin interface framework
- **Tkinter** - Desktop GUI for admin panel

## Database
- **PostgreSQL** with connection pooling
- Database URL configured via environment variables
- Auto-migration system in `db/base.py`
- Tables: courses, bookings, referral_coupons, referral_usage, events

## Deployment
- **Docker Compose** for local development (PostgreSQL container)
- **Heroku** deployment ready (Procfile included)
- Environment variables for configuration management
- Systemd service configuration available

## Development Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp config.py.example config.py
# Edit config.py with your values
```

### Running Services
```bash
# Start bot
python bot.py
# or
./run.sh

# Start web admin (port 5000)
python web_admin.py

# Start desktop admin
python admin_panel.py
```

### Database Management
```bash
# Auto-populate courses
python db_management/populate_initial_course.py

# Database setup is automatic on bot startup
```

## Configuration
- Environment variables preferred over hardcoded values
- `.env` file support for local development
- `config.py.example` template provided
- Sensitive data excluded from git via `.gitignore`