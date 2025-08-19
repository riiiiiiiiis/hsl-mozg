# bot.py
import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import config
from db.base import setup_database
from handlers import command_handlers, callback_handlers, message_handlers
from utils.notifications import schedule_all_lesson_notifications

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)





def main() -> None:
    """Основная функция для запуска бота."""
    # 1. СНАЧАЛА настраиваем базу данных. Это создаст все таблицы.
    try:
        setup_database()
        logger.info("Database setup was successful.")
        
        # Автообновление курсов при каждом деплое
        from db_management.populate_initial_course import main as update_courses
        update_courses()
        logger.info("Courses updated successfully.")
        
    except Exception as e:
        logger.critical(f"FATAL: Database setup failed. Bot cannot start. Error: {e}")
        return  # Не запускаем бота, если база не готова

    # 2. Создаем приложение бота
    application = Application.builder().token(config.BOT_TOKEN).build()

    # 3. Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", command_handlers.start_command))
    application.add_handler(CommandHandler("reset", command_handlers.reset_command))
    application.add_handler(CommandHandler("stats", command_handlers.stats_command))
    application.add_handler(CommandHandler("create_referral", command_handlers.create_referral_command))
    application.add_handler(CommandHandler("referral_stats", command_handlers.referral_stats_command))
    
    # 4. Регистрируем обработчик callback'ов от кнопок
    # Важно: здесь должен быть ОДИН обработчик-маршрутизатор
    # У вас в коде он называется main_callback_handler
    application.add_handler(CallbackQueryHandler(callback_handlers.main_callback_handler))

    # 5. Регистрируем обработчик фото (для чеков)
    application.add_handler(MessageHandler(filters.PHOTO, message_handlers.photo_handler))
    
    # 6. Регистрируем обработчик для всех остальных сообщений (текст, видео, документы и т.д.)
    # Этот handler должен быть последним, чтобы не перехватывать команды
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & ~filters.PHOTO, 
        message_handlers.any_message_handler
    ))

    # 7. Планируем уведомления для всех активных уроков при старте
    async def startup_callback(application):
        """Планирует уведомления для всех активных уроков при старте бота."""
        logger.info("Bot started, scheduling lesson notifications...")
        try:
            await schedule_all_lesson_notifications(application)
            logger.info("All lesson notifications scheduled successfully")
        except Exception as e:
            logger.error(f"Error scheduling notifications: {e}")

    # Добавляем callback для выполнения при старте
    application.post_init = startup_callback

    # 8. Запускаем бота
    logger.info("Starting bot polling...")
    application.run_polling()


if __name__ == "__main__":
    main()