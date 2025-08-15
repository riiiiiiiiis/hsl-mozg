#!/usr/bin/env python3
"""
Test for lesson type separation functionality.
Ensures users registered for previous lessons can register for new lessons.
"""

import unittest
from unittest.mock import patch, MagicMock
from db import free_lessons


class TestLessonTypeSeparation(unittest.TestCase):
    """Test suite for lesson type separation."""

    @patch('db.free_lessons.get_db_connection')
    def test_user_can_register_for_new_lesson_type(self, mock_get_connection):
        """Test that user registered for vibecoding_lesson can register for cursor_lesson."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Simulate user registered for vibecoding_lesson but not cursor_lesson
        def mock_fetchone_side_effect(*args, **kwargs):
            # Get the SQL query and parameters
            sql_call = mock_cursor.execute.call_args[0]
            if len(sql_call) > 1:
                lesson_type = sql_call[1][1]  # Second parameter is lesson_type
                if lesson_type == 'vibecoding_lesson':
                    return {'id': 1}  # User is registered for vibecoding
                elif lesson_type == 'cursor_lesson':
                    return None  # User is NOT registered for cursor
            return None
        
        mock_cursor.fetchone.side_effect = mock_fetchone_side_effect
        
        # Test: User should NOT be registered for cursor_lesson
        is_registered_cursor = free_lessons.is_user_registered_for_lesson_type(12345, 'cursor_lesson')
        self.assertFalse(is_registered_cursor)
        
        # Test: User should be registered for vibecoding_lesson
        is_registered_vibecoding = free_lessons.is_user_registered_for_lesson_type(12345, 'vibecoding_lesson')
        self.assertTrue(is_registered_vibecoding)

    @patch('db.free_lessons.get_db_connection')
    def test_user_registered_for_cursor_cannot_register_again(self, mock_get_connection):
        """Test that user already registered for cursor_lesson cannot register again."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Simulate user registered for cursor_lesson
        mock_cursor.fetchone.return_value = {'id': 1}
        
        # Test: User should be registered for cursor_lesson
        is_registered = free_lessons.is_user_registered_for_lesson_type(12345, 'cursor_lesson')
        self.assertTrue(is_registered)

    @patch('db.free_lessons.get_db_connection')
    def test_get_registration_by_user_and_type(self, mock_get_connection):
        """Test getting registration by user and lesson type."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock registration data
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'user_id': 12345,
            'email': 'test@example.com',
            'lesson_type': 'cursor_lesson'
        }
        
        # Test getting cursor lesson registration
        registration = free_lessons.get_registration_by_user_and_type(12345, 'cursor_lesson')
        
        self.assertIsNotNone(registration)
        self.assertEqual(registration['lesson_type'], 'cursor_lesson')
        self.assertEqual(registration['email'], 'test@example.com')
        
        # Verify correct SQL was called
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('WHERE user_id = %s AND lesson_type = %s', call_args[0])
        self.assertEqual(call_args[1], (12345, 'cursor_lesson'))

    @patch('db.free_lessons.get_db_connection')
    def test_invalid_lesson_type_handling(self, mock_get_connection):
        """Test handling of invalid lesson types."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Test with invalid lesson type
        is_registered = free_lessons.is_user_registered_for_lesson_type(12345, 'invalid_lesson')
        self.assertFalse(is_registered)
        
        # Verify database was not called for invalid lesson type
        mock_cursor.execute.assert_not_called()

    def test_lesson_type_separation_scenario(self):
        """Test complete scenario: user registered for old lesson can register for new."""
        with patch('db.free_lessons.get_db_connection') as mock_get_connection:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_get_connection.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Scenario: User has vibecoding_lesson registration
            def mock_fetchone_for_check(*args, **kwargs):
                sql_call = mock_cursor.execute.call_args[0]
                if len(sql_call) > 1 and len(sql_call[1]) > 1:
                    lesson_type = sql_call[1][1]
                    if lesson_type == 'cursor_lesson':
                        return None  # Not registered for cursor
                    elif lesson_type == 'vibecoding_lesson':
                        return {'id': 1}  # Registered for vibecoding
                return None
            
            mock_cursor.fetchone.side_effect = mock_fetchone_for_check
            
            # User should be able to register for cursor lesson
            can_register_cursor = not free_lessons.is_user_registered_for_lesson_type(12345, 'cursor_lesson')
            self.assertTrue(can_register_cursor)
            
            # User should already be registered for vibecoding lesson
            already_registered_vibecoding = free_lessons.is_user_registered_for_lesson_type(12345, 'vibecoding_lesson')
            self.assertTrue(already_registered_vibecoding)

    def test_backward_compatibility(self):
        """Test that old functions still work for general checks."""
        with patch('db.free_lessons.get_db_connection') as mock_get_connection:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_get_connection.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock that user has some registration
            mock_cursor.fetchone.return_value = {'id': 1}
            
            # Old function should still work
            is_registered = free_lessons.is_user_registered(12345)
            self.assertTrue(is_registered)


if __name__ == '__main__':
    print("Testing lesson type separation functionality...")
    unittest.main(verbosity=2)