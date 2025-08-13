#!/usr/bin/env python3
"""
Простые тесты для функциональности бесплатного урока (без БД).
"""

import unittest
import sys
import os
import re

# Добавляем корневую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import constants


def validate_email_simple(email):
    """Простая валидация email без импорта модулей БД."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


class TestFreeLessonSimple(unittest.TestCase):
    """Простые тесты без подключения к БД."""
    
    def test_email_validation(self):
        """Тест валидации email адресов."""
        # Корректные email
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk", 
            "user+tag@example.org",
            "123@test.com"
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(
                    validate_email_simple(email),
                    f"Email {email} должен быть валидным"
                )
        
        # Некорректные email
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "",
            "test@.com",
            "test@com"
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(
                    validate_email_simple(email),
                    f"Email {email} должен быть невалидным"
                )
    
    def test_constants_structure(self):
        """Тест структуры констант бесплатного урока."""
        # Проверяем, что все необходимые константы определены
        self.assertIn('FREE_LESSON', dir(constants))
        
        free_lesson = constants.FREE_LESSON
        required_fields = ['title', 'button_text', 'description', 'date_text', 'google_meet_link', 'is_active']
        
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, free_lesson, f"Поле {field} должно быть в FREE_LESSON")
                self.assertIsNotNone(free_lesson[field], f"Поле {field} не должно быть None")
        
        # Проверяем типы данных
        self.assertIsInstance(free_lesson['title'], str)
        self.assertIsInstance(free_lesson['button_text'], str)
        self.assertIsInstance(free_lesson['description'], str)
        self.assertIsInstance(free_lesson['date_text'], str)
        self.assertIsInstance(free_lesson['google_meet_link'], str)
        self.assertIsInstance(free_lesson['is_active'], bool)
        
        # Проверяем, что ссылка Google Meet имеет правильный формат
        self.assertTrue(
            free_lesson['google_meet_link'].startswith('https://meet.google.com/'),
            "Ссылка Google Meet должна начинаться с https://meet.google.com/"
        )
    
    def test_callback_constants(self):
        """Тест констант для callback'ов."""
        # Проверяем, что новые callback константы определены
        self.assertTrue(hasattr(constants, 'CALLBACK_FREE_LESSON_INFO'))
        self.assertTrue(hasattr(constants, 'CALLBACK_FREE_LESSON_REGISTER'))
        
        # Проверяем, что они имеют правильный тип
        self.assertIsInstance(constants.CALLBACK_FREE_LESSON_INFO, str)
        self.assertIsInstance(constants.CALLBACK_FREE_LESSON_REGISTER, str)
        
        # Проверяем, что они не пустые
        self.assertNotEqual(constants.CALLBACK_FREE_LESSON_INFO, "")
        self.assertNotEqual(constants.CALLBACK_FREE_LESSON_REGISTER, "")
    
    def test_free_lesson_messages(self):
        """Тест сообщений для бесплатного урока."""
        # Проверяем, что все сообщения определены
        message_constants = [
            'FREE_LESSON_EMAIL_REQUEST',
            'FREE_LESSON_EMAIL_INVALID', 
            'FREE_LESSON_REGISTRATION_SUCCESS',
            'FREE_LESSON_ALREADY_REGISTERED',
            'FREE_LESSON_REMINDER'
        ]
        
        for msg_const in message_constants:
            with self.subTest(constant=msg_const):
                self.assertTrue(hasattr(constants, msg_const), f"Константа {msg_const} должна быть определена")
                msg_value = getattr(constants, msg_const)
                self.assertIsInstance(msg_value, str, f"Константа {msg_const} должна быть строкой")
                self.assertNotEqual(msg_value, "", f"Константа {msg_const} не должна быть пустой")


def run_simple_tests():
    """Запуск простых тестов."""
    print("🧪 Запуск простых тестов для бесплатного урока...")
    
    # Создаём test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFreeLessonSimple)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Выводим результаты
    if result.wasSuccessful():
        print(f"\n✅ Все простые тесты прошли успешно! Выполнено {result.testsRun} тестов.")
        return True
    else:
        print(f"\n❌ Некоторые тесты не прошли. Выполнено {result.testsRun} тестов.")
        print(f"Ошибки: {len(result.errors)}, Неудачи: {len(result.failures)}")
        return False


if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)