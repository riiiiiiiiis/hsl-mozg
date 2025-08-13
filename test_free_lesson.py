#!/usr/bin/env python3
"""
Интеграционные тесты для функциональности бесплатного урока.
"""

import unittest
import sys
import os

# Добавляем корневую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import free_lessons as db_free_lessons
import constants


class TestFreeLessonIntegration(unittest.TestCase):
    """Тесты для интеграции функциональности бесплатного урока."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        # Используем тестовые ID пользователей
        self.test_user_id = 999999999
        self.test_email = "test@example.com"
        self.test_username = "testuser"
        self.test_first_name = "Test User"
    
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
                    db_free_lessons.validate_email(email),
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
                    db_free_lessons.validate_email(email),
                    f"Email {email} должен быть невалидным"
                )
    
    def test_registration_creation(self):
        """Тест создания регистрации на бесплатный урок."""
        # Проверяем, что пользователь изначально не зарегистрирован
        self.assertFalse(
            db_free_lessons.is_user_registered(self.test_user_id),
            "Пользователь не должен быть зарегистрирован изначально"
        )
        
        # Создаём регистрацию
        registration_id = db_free_lessons.create_free_lesson_registration(
            self.test_user_id,
            self.test_username,
            self.test_first_name,
            self.test_email
        )
        
        self.assertIsNotNone(registration_id, "Регистрация должна быть создана")
        self.assertIsInstance(registration_id, int, "ID регистрации должен быть числом")
        
        # Проверяем, что пользователь теперь зарегистрирован
        self.assertTrue(
            db_free_lessons.is_user_registered(self.test_user_id),
            "Пользователь должен быть зарегистрирован после создания регистрации"
        )
        
        # Получаем данные регистрации
        registration = db_free_lessons.get_registration_by_user(self.test_user_id)
        self.assertIsNotNone(registration, "Регистрация должна быть найдена")
        self.assertEqual(registration['user_id'], self.test_user_id)
        self.assertEqual(registration['email'], self.test_email)
        self.assertEqual(registration['username'], self.test_username)
        self.assertEqual(registration['first_name'], self.test_first_name)
        self.assertFalse(registration['notification_sent'])
    
    def test_duplicate_registration(self):
        """Тест обработки повторной регистрации."""
        # Создаём первую регистрацию
        first_registration_id = db_free_lessons.create_free_lesson_registration(
            self.test_user_id,
            self.test_username,
            self.test_first_name,
            self.test_email
        )
        
        self.assertIsNotNone(first_registration_id)
        
        # Создаём повторную регистрацию с другим email
        new_email = "newemail@example.com"
        second_registration_id = db_free_lessons.create_free_lesson_registration(
            self.test_user_id,
            self.test_username,
            self.test_first_name,
            new_email
        )
        
        self.assertIsNotNone(second_registration_id)
        
        # Проверяем, что email обновился
        registration = db_free_lessons.get_registration_by_user(self.test_user_id)
        self.assertEqual(registration['email'], new_email)
        
        # Проверяем, что notification_sent сбросился
        self.assertFalse(registration['notification_sent'])
    
    def test_notification_marking(self):
        """Тест отметки уведомления как отправленного."""
        # Создаём регистрацию
        registration_id = db_free_lessons.create_free_lesson_registration(
            self.test_user_id,
            self.test_username,
            self.test_first_name,
            self.test_email
        )
        
        # Проверяем, что уведомление изначально не отправлено
        registration = db_free_lessons.get_registration_by_user(self.test_user_id)
        self.assertFalse(registration['notification_sent'])
        
        # Отмечаем уведомление как отправленное
        result = db_free_lessons.mark_notification_sent(registration_id)
        self.assertTrue(result, "Отметка уведомления должна быть успешной")
        
        # Проверяем, что статус обновился
        updated_registration = db_free_lessons.get_registration_by_user(self.test_user_id)
        self.assertTrue(updated_registration['notification_sent'])
    
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
    
    def tearDown(self):
        """Очистка после каждого теста."""
        # Удаляем тестовую регистрацию, если она была создана
        try:
            # Простая очистка - в реальном проекте лучше использовать транзакции
            from db.base import get_db_connection
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM free_lesson_registrations WHERE user_id = %s", (self.test_user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not clean up test data: {e}")


def run_tests():
    """Запуск всех тестов."""
    print("Запуск интеграционных тестов для бесплатного урока...")
    
    # Создаём test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFreeLessonIntegration)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Выводим результаты
    if result.wasSuccessful():
        print(f"\n✅ Все тесты прошли успешно! Выполнено {result.testsRun} тестов.")
        return True
    else:
        print(f"\n❌ Некоторые тесты не прошли. Выполнено {result.testsRun} тестов.")
        print(f"Ошибки: {len(result.errors)}, Неудачи: {len(result.failures)}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)