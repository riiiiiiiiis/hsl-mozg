#!/usr/bin/env python3
"""
Скрипт для отправки ссылки на урок по Cursor всем зарегистрированным пользователям
"""

import asyncio
import logging
import os
from telegram import Bot
from db import free_lessons as db_free_lessons
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_lesson_links():
    """Отправляет ссылку на урок всем зарегистрированным на cursor_lesson"""
    
    bot = Bot(token=config.BOT_TOKEN)
    
    # Получаем всех зарегистрированных на урок по Cursor
    registrations = db_free_lessons.get_registrations_by_type('cursor_lesson')
    
    if not registrations:
        logger.info("Нет зарегистрированных пользователей на урок по Cursor")
        return
    
    message_text = """🔔 Напоминание о бесплатном уроке!

📅 ВАЙБКОДИНГ С CURSOR
⏰ 20 августа в 21:00 по МСК

Создадим телеграм бота с помощью промтинга в Cursor!

👉 Ссылка на урок: https://meet.google.com/cna-qrtp-wna

До встречи на уроке! 🚀"""
    
    success_count = 0
    error_count = 0
    
    for registration in registrations:
        user_id = registration['user_id']
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message_text
            )
            logger.info(f"Отправлено пользователю {user_id}")
            success_count += 1
            # Небольшая задержка между отправками
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
            error_count += 1
    
    logger.info(f"Отправка завершена. Успешно: {success_count}, Ошибок: {error_count}")
    print(f"\n✅ Отправлено {success_count} пользователям")
    if error_count > 0:
        print(f"⚠️ Не удалось отправить {error_count} пользователям")

if __name__ == "__main__":
    asyncio.run(send_lesson_links())