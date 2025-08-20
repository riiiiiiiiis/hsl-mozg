"""
Утилита для отправки ссылки на урок по Cursor всем зарегистрированным пользователям
"""

import logging
import asyncio
from telegram import Bot
from db import free_lessons as db_free_lessons

logger = logging.getLogger(__name__)

async def send_cursor_lesson_link(bot: Bot):
    """
    Отправляет ссылку на урок по Cursor всем зарегистрированным пользователям.
    Вызывается при деплое бота.
    """
    
    # Получаем всех зарегистрированных на урок по Cursor
    registrations = db_free_lessons.get_registrations_by_type('cursor_lesson')
    
    if not registrations:
        logger.info("No users registered for Cursor lesson")
        return
    
    message_text = """🔔 Важное обновление!

📅 ВАЙБКОДИНГ С CURSOR
⏰ 20 августа в 21:00 по МСК

Обновлена ссылка на урок:
👉 https://meet.google.com/cna-qrtp-wna

Сохраните новую ссылку и до встречи на уроке! 🚀"""
    
    success_count = 0
    error_count = 0
    
    for registration in registrations:
        user_id = registration['user_id']
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message_text
            )
            logger.info(f"Sent cursor lesson link to user {user_id}")
            success_count += 1
            # Небольшая задержка между отправками чтобы не спамить
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to send to user {user_id}: {e}")
            error_count += 1
    
    logger.info(f"Cursor lesson link sent. Success: {success_count}, Errors: {error_count}")