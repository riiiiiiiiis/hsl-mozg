#!/usr/bin/env python3
"""
Mock тестирование бота без реальной БД.
"""

import asyncio
from unittest.mock import Mock, AsyncMock
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import constants
from handlers.callback_handlers import handle_free_lesson_info, handle_free_lesson_register
from handlers.message_handlers import handle_email_input


class MockQuery:
    """Mock объект для callback query."""
    def __init__(self, data, user_id=12345):
        self.data = data
        self.from_user = Mock()
        self.from_user.id = user_id
        self.from_user.username = "testuser"
        self.from_user.first_name = "Test User"
        self.edit_message_text = AsyncMock()
        self.answer = AsyncMock()


class MockUpdate:
    """Mock объект для update."""
    def __init__(self, text=None, user_id=12345):
        self.message = Mock()
        self.message.from_user = Mock()
        self.message.from_user.id = user_id
        self.message.from_user.username = "testuser"
        self.message.from_user.first_name = "Test User"
        self.message.text = text
        self.message.reply_text = AsyncMock()


class MockContext:
    """Mock объект для context."""
    def __init__(self):
        self.user_data = {
            'user_id': 12345,
            'username': 'testuser',
            'first_name': 'Test User'
        }


async def test_free_lesson_flow():
    """Тестирование полного потока бесплатного урока."""
    print("🧪 Тестирование потока бесплатного урока...")
    
    # Mock для БД функций
    import db.free_lessons as db_free_lessons
    import db.events as db_events
    
    # Заменяем функции БД на mock'и
    original_is_registered = db_free_lessons.is_user_registered
    original_get_registration = db_free_lessons.get_registration_by_user
    original_create_registration = db_free_lessons.create_free_lesson_registration
    original_log_event = db_events.log_event
    
    db_free_lessons.is_user_registered = Mock(return_value=False)
    db_free_lessons.get_registration_by_user = Mock(return_value=None)
    db_free_lessons.create_free_lesson_registration = Mock(return_value=123)
    db_events.log_event = Mock()
    
    try:
        # 1. Тест просмотра информации о бесплатном уроке
        print("\n1️⃣ Тестирование просмотра информации...")
        query = MockQuery(constants.CALLBACK_FREE_LESSON_INFO)
        context = MockContext()
        
        await handle_free_lesson_info(query, context)
        
        # Проверяем, что сообщение было отредактировано
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args[1]
        
        print(f"✅ Сообщение отправлено: {call_args['text'][:100]}...")
        print(f"✅ Есть кнопка регистрации: {'reply_markup' in call_args}")
        
        # 2. Тест начала регистрации
        print("\n2️⃣ Тестирование начала регистрации...")
        query2 = MockQuery(constants.CALLBACK_FREE_LESSON_REGISTER)
        context2 = MockContext()
        
        await handle_free_lesson_register(query2, context2)
        
        # Проверяем, что состояние установлено
        print(f"✅ Состояние ожидания email: {context2.user_data.get('awaiting_free_lesson_email', False)}")
        
        # 3. Тест ввода email
        print("\n3️⃣ Тестирование ввода email...")
        update = MockUpdate("test@example.com")
        context3 = MockContext()
        context3.user_data['awaiting_free_lesson_email'] = True
        
        await handle_email_input(update, context3)
        
        # Проверяем, что регистрация была создана
        db_free_lessons.create_free_lesson_registration.assert_called_once()
        print("✅ Регистрация создана")
        
        # Проверяем, что состояние сброшено
        print(f"✅ Состояние сброшено: {'awaiting_free_lesson_email' not in context3.user_data}")
        
        # 4. Тест невалидного email
        print("\n4️⃣ Тестирование невалидного email...")
        update_invalid = MockUpdate("invalid-email")
        context4 = MockContext()
        context4.user_data['awaiting_free_lesson_email'] = True
        
        await handle_email_input(update_invalid, context4)
        
        # Проверяем, что отправлено сообщение об ошибке
        update_invalid.message.reply_text.assert_called_once()
        error_message = update_invalid.message.reply_text.call_args[0][0]
        print(f"✅ Сообщение об ошибке: {error_message[:50]}...")
        
        print("\n🎉 Все тесты прошли успешно!")
        
    finally:
        # Восстанавливаем оригинальные функции
        db_free_lessons.is_user_registered = original_is_registered
        db_free_lessons.get_registration_by_user = original_get_registration
        db_free_lessons.create_free_lesson_registration = original_create_registration
        db_events.log_event = original_log_event


if __name__ == "__main__":
    asyncio.run(test_free_lesson_flow())