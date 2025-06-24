import logging
import asyncio
import sys
import urllib.request
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PicklePersistence,
    filters,
    ContextTypes,
)

import config
import database
from handlers import command_handlers, callback_handlers, message_handlers

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_initialization(application: Application) -> None:
    """Runs after the bot is initialized, to clear any existing webhooks."""
    logger.info("Running post-initialization...")
    try:
        # Clear any pending updates and delete webhook
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook successfully deleted.")
    except Exception as e:
        logger.error(f"Error during webhook deletion: {e}")
    await asyncio.sleep(2)

def main() -> None:
    """Sets up and runs the Telegram bot."""
    logger.info("Starting bot setup...")
    
    # Ensure database tables are created before starting
    try:
        database.setup_database()
    except Exception as e:
        logger.critical(f"DATABASE SETUP FAILED: {e}. Aborting startup.")
        sys.exit(1)

    # Use PicklePersistence to save user_data across restarts
    persistence = PicklePersistence(filepath=config.PERSISTENCE_FILEPATH)
    
    # Build the bot application
    application = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .persistence(persistence)
        .post_init(post_initialization)
        .build()
    )

    # --- Register Handlers ---
    # Commands
    application.add_handler(CommandHandler("start", command_handlers.start_command))
    application.add_handler(CommandHandler("reset", command_handlers.reset_command))
    application.add_handler(CommandHandler("create_referral", command_handlers.create_referral_command))
    application.add_handler(CommandHandler("referral_stats", command_handlers.referral_stats_command))
    
    # Callback Queries (inline buttons)
    application.add_handler(CallbackQueryHandler(callback_handlers.main_callback_handler))

    # Messages (for photo uploads)
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, message_handlers.photo_handler))

    logger.info("Bot starting to poll for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot application has stopped.")

if __name__ == "__main__":
    main()