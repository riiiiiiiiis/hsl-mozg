#!/usr/bin/env python3
"""
Скрипт для отправки сообщений участникам с подтвержденной оплатой.
ВАЖНО: Сейчас отправка закомментирована! Раскомментируйте строки с bot.send_message для реальной отправки.
"""

import asyncio
import sqlite3
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
import config

def get_db_connection():
    """Создание подключения к базе данных"""
    return sqlite3.connect(config.DB_NAME)

def get_confirmed_participants():
    """Получить список всех участников с подтвержденной оплатой (confirmed = 2)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, username, first_name, chosen_course, course_id, created_at
        FROM bookings
        WHERE confirmed = 2
        ORDER BY created_at DESC
    """)
    
    participants = cursor.fetchall()
    conn.close()
    
    return participants

async def send_message_to_participants(message_text):
    """Отправить сообщение всем участникам с подтвержденной оплатой"""
    bot = Bot(token=config.BOT_TOKEN)
    participants = get_confirmed_participants()
    
    if not participants:
        print("❌ Нет участников с подтвержденной оплатой")
        return
    
    print(f"📨 Начинаю рассылку {len(participants)} участникам...\n")
    
    success_count = 0
    error_count = 0
    
    for user_id, username, first_name, chosen_course, course_id, created_at in participants:
        try:
            # Персонализированное сообщение
            personalized_message = message_text.replace("{first_name}", first_name or "Участник")
            personalized_message = personalized_message.replace("{course_name}", chosen_course)
            
            print(f"📤 Отправляю сообщение пользователю {user_id} (@{username or 'без username'})...")
            
            # ВАЖНО: Эта строка закомментирована для безопасности!
            # Раскомментируйте для реальной отправки:
            # await bot.send_message(
            #     chat_id=user_id,
            #     text=personalized_message,
            #     parse_mode=ParseMode.MARKDOWN_V2
            # )
            
            # Сейчас просто показываем, что бы отправили:
            print(f"✅ Сообщение для {first_name or 'Участник'} (@{username or 'без username'}):")
            print(f"   Курс: {chosen_course}")
            print(f"   Текст: {personalized_message[:100]}...")
            print()
            
            success_count += 1
            
            # Задержка между сообщениями (чтобы не превысить лимиты Telegram)
            await asyncio.sleep(0.5)
            
        except Exception as e:
            error_count += 1
            print(f"❌ Ошибка при отправке пользователю {user_id}: {e}")
    
    print(f"\n📊 Результаты рассылки:")
    print(f"✅ Успешно: {success_count}")
    print(f"❌ Ошибки: {error_count}")
    print(f"📨 Всего: {len(participants)}")

async def main():
    """Основная функция"""
    # Пример сообщения с возможностью персонализации
    message_template = """
Привет, {first_name}! 👋

Напоминаем, что ваше участие в курсе "{course_name}" подтверждено! 

🗓 Не забудьте отметить дату начала курса в календаре.
📚 Подготовьте все необходимое для успешного обучения.

Если у вас есть вопросы, свяжитесь с администратором: {admin_contact}

До встречи на курсе! 🚀
    """.strip()
    
    # Подставляем контакт админа
    message_template = message_template.replace("{admin_contact}", config.ADMIN_CONTACT)
    
    print("=" * 80)
    print("🤖 РЕЖИМ ТЕСТИРОВАНИЯ - СООБЩЕНИЯ НЕ ОТПРАВЛЯЮТСЯ!")
    print("=" * 80)
    print("\n📝 Шаблон сообщения:")
    print(message_template)
    print("\n" + "=" * 80 + "\n")
    
    # Запуск рассылки
    await send_message_to_participants(message_template)

if __name__ == "__main__":
    print("🚀 Запуск скрипта рассылки сообщений...\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹ Рассылка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")