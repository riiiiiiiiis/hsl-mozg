#!/usr/bin/env python3
"""
Tests for September course update functionality.
Tests updated constants, lesson types, and course stream tracking.
"""

import unittest
from unittest.mock import patch, MagicMock
import constants
from db import free_lessons, bookings


class TestSeptemberUpdate(unittest.TestCase):
    """Test suite for September course update."""

    def test_course_constants_updated(self):
        """Test that course constants have been updated with September dates and 4th stream."""
        # Test that we have courses
        self.assertGreater(len(constants.COURSES), 0)
        
        for course in constants.COURSES:
            # Test required fields exist
            self.assertIn('id', course)
            self.assertIn('name', course)
            self.assertIn('description', course)
            self.assertIn('start_date_text', course)
            
            # Test that start date is updated to September
            self.assertEqual(course['start_date_text'], '1 сентября')
            
            # Test that description contains 4th stream branding
            self.assertIn('ЧЕТВЕРТЫЙ ПОТОК', course['description'])
            
            # Test that description mentions weekly schedule
            self.assertIn('каждую неделю', course['description'])

    def test_free_lesson_constants_updated(self):
        """Test that free lesson constants have been updated for Cursor lesson."""
        free_lesson = constants.FREE_LESSON
        
        # Test title and button text updated
        self.assertEqual(free_lesson['title'], 'Вайбкодинг с Cursor')
        self.assertEqual(free_lesson['button_text'], '🆓 Вайбкодинг с Cursor')
        
        # Test description mentions Cursor
        self.assertIn('CURSOR', free_lesson['description'])
        self.assertIn('Cursor', free_lesson['description'])
        
        # Test date is updated
        self.assertEqual(free_lesson['date_text'], '2 сентября в 21:00 по МСК')
        
        # Test lesson is active
        self.assertTrue(free_lesson['is_active'])

    @patch('db.free_lessons.get_db_connection')
    def test_create_free_lesson_with_lesson_type(self, mock_get_connection):
        """Test creating free lesson registration with lesson type."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'id': 123}
        
        # Test with default lesson type
        result = free_lessons.create_free_lesson_registration(
            user_id=12345,
            username='testuser',
            first_name='Test',
            email='test@example.com'
        )
        
        self.assertEqual(result, 123)
        
        # Verify SQL was called with correct parameters
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('lesson_type', call_args[0])  # SQL contains lesson_type
        self.assertEqual(call_args[1][4], 'cursor_lesson')  # Default lesson type
        
        # Test with specific lesson type
        free_lessons.create_free_lesson_registration(
            user_id=12346,
            username='testuser2',
            first_name='Test2',
            email='test2@example.com',
            lesson_type='vibecoding_lesson'
        )
        
        # Verify vibecoding_lesson was used
        call_args = mock_cursor.execute.call_args[0]
        self.assertEqual(call_args[1][4], 'vibecoding_lesson')

    @patch('db.free_lessons.get_db_connection')
    def test_get_registrations_by_type(self, mock_get_connection):
        """Test filtering registrations by lesson type."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock return data
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'user_id': 123, 'lesson_type': 'cursor_lesson'},
            {'id': 2, 'user_id': 124, 'lesson_type': 'cursor_lesson'}
        ]
        
        # Test getting cursor lesson registrations
        result = free_lessons.get_registrations_by_type('cursor_lesson')
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['lesson_type'], 'cursor_lesson')
        
        # Verify SQL was called with correct filter
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('WHERE lesson_type = %s', call_args[0])
        self.assertEqual(call_args[1][0], 'cursor_lesson')

    @patch('db.bookings.get_db_connection')
    def test_create_booking_with_course_stream(self, mock_get_connection):
        """Test creating booking with course stream tracking."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'id': 456}
        
        # Test with default course stream
        result = bookings.create_booking(
            user_id=12345,
            username='testuser',
            first_name='Test',
            course_id=1,
            referral_code=None,
            discount_percent=0
        )
        
        self.assertEqual(result, 456)
        
        # Verify SQL was called with course_stream
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('course_stream', call_args[0])  # SQL contains course_stream
        self.assertEqual(call_args[1][6], '4th_stream')  # Default course stream
        
        # Test with specific course stream
        bookings.create_booking(
            user_id=12346,
            username='testuser2',
            first_name='Test2',
            course_id=1,
            referral_code=None,
            discount_percent=0,
            course_stream='3rd_stream'
        )
        
        # Verify 3rd_stream was used
        call_args = mock_cursor.execute.call_args[0]
        self.assertEqual(call_args[1][6], '3rd_stream')

    @patch('db.bookings.get_db_connection')
    def test_get_bookings_by_stream(self, mock_get_connection):
        """Test filtering bookings by course stream."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock return data
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'user_id': 123, 'course_stream': '4th_stream', 'course_name': 'Вайб кодинг'},
            {'id': 2, 'user_id': 124, 'course_stream': '4th_stream', 'course_name': 'Вайб кодинг EXTRA'}
        ]
        
        # Test getting 4th stream bookings
        result = bookings.get_bookings_by_stream('4th_stream')
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['course_stream'], '4th_stream')
        
        # Verify SQL was called with correct filter
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('WHERE b.course_stream = %s', call_args[0])
        self.assertEqual(call_args[1][0], '4th_stream')

    def test_lesson_type_validation(self):
        """Test that lesson type validation works correctly."""
        with patch('db.free_lessons.get_db_connection') as mock_get_connection:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_get_connection.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = {'id': 123}
            
            # Test with invalid lesson type - should default to cursor_lesson
            result = free_lessons.create_free_lesson_registration(
                user_id=12345,
                username='testuser',
                first_name='Test',
                email='test@example.com',
                lesson_type='invalid_lesson'
            )
            
            # Should still create registration with default type
            self.assertEqual(result, 123)
            
            # Verify default lesson_type was used
            call_args = mock_cursor.execute.call_args[0]
            self.assertEqual(call_args[1][4], 'cursor_lesson')

    @patch('db.free_lessons.get_db_connection')
    def test_get_registration_stats(self, mock_get_connection):
        """Test getting registration statistics by lesson type."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock return data
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
        
        # Test getting statistics
        result = free_lessons.get_registration_stats()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['lesson_type'], 'cursor_lesson')
        self.assertEqual(result[0]['total_registrations'], 5)
        self.assertEqual(result[1]['lesson_type'], 'vibecoding_lesson')
        self.assertEqual(result[1]['total_registrations'], 10)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)