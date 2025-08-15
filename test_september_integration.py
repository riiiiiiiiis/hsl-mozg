#!/usr/bin/env python3
"""
Integration tests for September course update.
Tests the complete system with updated constants and functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import constants
from db import free_lessons, bookings


class TestSeptemberIntegration(unittest.TestCase):
    """Integration test suite for September course update."""

    def test_course_information_consistency(self):
        """Test that all course information is consistent across the system."""
        # Test that both courses have consistent September dates
        for course in constants.COURSES:
            self.assertEqual(course['start_date_text'], '1 сентября')
            self.assertIn('ЧЕТВЕРТЫЙ ПОТОК', course['description'])
            self.assertIn('1 сентября', course['description'])
            self.assertIn('каждую неделю', course['description'])

    def test_free_lesson_information_consistency(self):
        """Test that free lesson information is consistent."""
        free_lesson = constants.FREE_LESSON
        
        # Test all fields are updated consistently
        self.assertEqual(free_lesson['title'], 'Вайбкодинг с Cursor')
        self.assertEqual(free_lesson['button_text'], '🆓 Вайбкодинг с Cursor')
        self.assertIn('CURSOR', free_lesson['description'])
        self.assertEqual(free_lesson['date_text'], '2 сентября в 21:00 по МСК')
        self.assertTrue(free_lesson['is_active'])

    def test_callback_constants_exist(self):
        """Test that all required callback constants exist."""
        required_callbacks = [
            'CALLBACK_FREE_LESSON_INFO',
            'CALLBACK_FREE_LESSON_REGISTER',
            'CALLBACK_SELECT_COURSE_PREFIX',
            'CALLBACK_CONFIRM_COURSE_SELECTION'
        ]
        
        for callback in required_callbacks:
            self.assertTrue(hasattr(constants, callback))
            self.assertIsInstance(getattr(constants, callback), str)

    def test_free_lesson_messages_exist(self):
        """Test that all free lesson message constants exist."""
        required_messages = [
            'FREE_LESSON_EMAIL_REQUEST',
            'FREE_LESSON_EMAIL_INVALID',
            'FREE_LESSON_REGISTRATION_SUCCESS',
            'FREE_LESSON_ALREADY_REGISTERED'
        ]
        
        for message in required_messages:
            self.assertTrue(hasattr(constants, message))
            self.assertIsInstance(getattr(constants, message), str)

    @patch('db.free_lessons.get_db_connection')
    def test_complete_free_lesson_registration_flow(self, mock_get_connection):
        """Test complete free lesson registration flow with new lesson types."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Test new registration (should get cursor_lesson type)
        mock_cursor.fetchone.return_value = {'id': 123}
        
        registration_id = free_lessons.create_free_lesson_registration(
            user_id=12345,
            username='testuser',
            first_name='Test User',
            email='test@example.com'
        )
        
        self.assertEqual(registration_id, 123)
        
        # Verify SQL was called with cursor_lesson type
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('lesson_type', call_args[0])
        self.assertEqual(call_args[1][4], 'cursor_lesson')  # lesson_type parameter

    @patch('db.bookings.get_db_connection')
    def test_complete_booking_flow_with_stream(self, mock_get_connection):
        """Test complete booking flow with course stream tracking."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Test new booking (should get 4th_stream)
        mock_cursor.fetchone.return_value = {'id': 456}
        
        booking_id = bookings.create_booking(
            user_id=12345,
            username='testuser',
            first_name='Test User',
            course_id=1,
            referral_code=None,
            discount_percent=0
        )
        
        self.assertEqual(booking_id, 456)
        
        # Verify SQL was called with 4th_stream
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('course_stream', call_args[0])
        self.assertEqual(call_args[1][6], '4th_stream')  # course_stream parameter

    @patch('db.free_lessons.get_db_connection')
    def test_lesson_type_filtering_works(self, mock_get_connection):
        """Test that lesson type filtering works correctly."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock cursor lesson registrations
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'user_id': 123, 'lesson_type': 'cursor_lesson', 'email': 'user1@test.com'},
            {'id': 2, 'user_id': 124, 'lesson_type': 'cursor_lesson', 'email': 'user2@test.com'}
        ]
        
        cursor_registrations = free_lessons.get_registrations_by_type('cursor_lesson')
        
        self.assertEqual(len(cursor_registrations), 2)
        for reg in cursor_registrations:
            self.assertEqual(reg['lesson_type'], 'cursor_lesson')
        
        # Verify correct SQL filter was used
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('WHERE lesson_type = %s', call_args[0])
        self.assertEqual(call_args[1][0], 'cursor_lesson')

    @patch('db.bookings.get_db_connection')
    def test_course_stream_filtering_works(self, mock_get_connection):
        """Test that course stream filtering works correctly."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock 4th stream bookings
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'user_id': 123, 'course_stream': '4th_stream', 'course_name': 'Вайб кодинг'},
            {'id': 2, 'user_id': 124, 'course_stream': '4th_stream', 'course_name': 'Вайб кодинг EXTRA'}
        ]
        
        fourth_stream_bookings = bookings.get_bookings_by_stream('4th_stream')
        
        self.assertEqual(len(fourth_stream_bookings), 2)
        for booking in fourth_stream_bookings:
            self.assertEqual(booking['course_stream'], '4th_stream')
        
        # Verify correct SQL filter was used
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('WHERE b.course_stream = %s', call_args[0])
        self.assertEqual(call_args[1][0], '4th_stream')

    @patch('db.free_lessons.get_db_connection')
    def test_statistics_functions_work(self, mock_get_connection):
        """Test that statistics functions return proper data structure."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock statistics data
        mock_cursor.fetchall.return_value = [
            {
                'lesson_type': 'cursor_lesson',
                'total_registrations': 5,
                'notifications_sent': 2,
                'pending_notifications': 3
            },
            {
                'lesson_type': 'vibecoding_lesson',
                'total_registrations': 10,
                'notifications_sent': 8,
                'pending_notifications': 2
            }
        ]
        
        stats = free_lessons.get_registration_stats()
        
        self.assertEqual(len(stats), 2)
        
        # Test cursor lesson stats
        cursor_stats = next(s for s in stats if s['lesson_type'] == 'cursor_lesson')
        self.assertEqual(cursor_stats['total_registrations'], 5)
        self.assertEqual(cursor_stats['notifications_sent'], 2)
        self.assertEqual(cursor_stats['pending_notifications'], 3)
        
        # Test vibecoding lesson stats
        vibecoding_stats = next(s for s in stats if s['lesson_type'] == 'vibecoding_lesson')
        self.assertEqual(vibecoding_stats['total_registrations'], 10)
        self.assertEqual(vibecoding_stats['notifications_sent'], 8)
        self.assertEqual(vibecoding_stats['pending_notifications'], 2)

    def test_email_validation_still_works(self):
        """Test that email validation functionality is preserved."""
        # Test valid emails
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'test123@test-domain.org'
        ]
        
        for email in valid_emails:
            self.assertTrue(free_lessons.validate_email(email))
        
        # Test invalid emails
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'test@',
            'test.domain.com',
            ''
        ]
        
        for email in invalid_emails:
            self.assertFalse(free_lessons.validate_email(email))

    def test_course_data_structure_integrity(self):
        """Test that course data structure has all required fields."""
        required_fields = ['id', 'name', 'button_text', 'description', 'price_usd']
        
        for course in constants.COURSES:
            for field in required_fields:
                self.assertIn(field, course, f"Course {course.get('name', 'Unknown')} missing field: {field}")
                self.assertIsNotNone(course[field], f"Course {course.get('name', 'Unknown')} has None value for field: {field}")
            
            # Test specific field types
            self.assertIsInstance(course['id'], int)
            self.assertIsInstance(course['price_usd'], int)
            self.assertIsInstance(course['name'], str)
            self.assertIsInstance(course['description'], str)

    def test_system_ready_for_deployment(self):
        """Test that the system is ready for deployment with all updates."""
        # Test that constants are properly formatted
        self.assertIsInstance(constants.COURSES, list)
        self.assertGreater(len(constants.COURSES), 0)
        self.assertIsInstance(constants.FREE_LESSON, dict)
        
        # Test that all courses have September dates
        for course in constants.COURSES:
            self.assertEqual(course['start_date_text'], '1 сентября')
        
        # Test that free lesson has Cursor branding
        self.assertEqual(constants.FREE_LESSON['title'], 'Вайбкодинг с Cursor')
        
        # Test that callback constants exist
        self.assertTrue(hasattr(constants, 'CALLBACK_FREE_LESSON_INFO'))
        self.assertTrue(hasattr(constants, 'CALLBACK_FREE_LESSON_REGISTER'))
        
        print("✅ System validation complete:")
        print(f"   - {len(constants.COURSES)} courses updated with September dates")
        print(f"   - Free lesson updated to '{constants.FREE_LESSON['title']}'")
        print(f"   - All callback constants present")
        print(f"   - Database functions support lesson types and course streams")
        print("   - System ready for deployment!")


if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)