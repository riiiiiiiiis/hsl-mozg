"""
Unit tests for utility functions in utils.py.

Tests the enhanced user identification and course flow information functions:
- get_user_identification() with proper priority handling
- get_course_flow_info() with Russian ordinal formatting
- Edge cases and error handling
"""

import unittest
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import get_user_identification, get_course_flow_info


class TestUserIdentification(unittest.TestCase):
    """Test cases for get_user_identification function."""

    def test_username_priority(self):
        """Test that username has highest priority when available."""
        user_data = {
            'username': 'john_doe',
            'first_name': 'John',
            'user_id': 123456
        }
        result = get_user_identification(user_data)
        self.assertEqual(result, '@john_doe')

    def test_first_name_priority_when_no_username(self):
        """Test that first_name is used when username is not available."""
        user_data = {
            'first_name': 'John',
            'user_id': 123456
        }
        result = get_user_identification(user_data)
        self.assertEqual(result, 'John')

    def test_user_id_fallback(self):
        """Test that user_id is used as fallback when other fields are missing."""
        user_data = {
            'user_id': 123456
        }
        result = get_user_identification(user_data)
        self.assertEqual(result, 'ID: 123456')

    def test_empty_username_handling(self):
        """Test that empty username is treated as missing."""
        user_data = {
            'username': '',
            'first_name': 'John',
            'user_id': 123456
        }
        result = get_user_identification(user_data)
        self.assertEqual(result, 'John')

    def test_whitespace_username_handling(self):
        """Test that whitespace-only username is treated as missing."""
        user_data = {
            'username': '   ',
            'first_name': 'John',
            'user_id': 123456
        }
        result = get_user_identification(user_data)
        self.assertEqual(result, 'John')

    def test_empty_first_name_handling(self):
        """Test that empty first_name is treated as missing."""
        user_data = {
            'username': '',
            'first_name': '',
            'user_id': 123456
        }
        result = get_user_identification(user_data)
        self.assertEqual(result, 'ID: 123456')

    def test_none_values_handling(self):
        """Test that None values are handled correctly."""
        user_data = {
            'username': None,
            'first_name': None,
            'user_id': 123456
        }
        result = get_user_identification(user_data)
        self.assertEqual(result, 'ID: 123456')

    def test_empty_dict_handling(self):
        """Test that empty dictionary returns 'Unknown User'."""
        user_data = {}
        result = get_user_identification(user_data)
        self.assertEqual(result, 'Unknown User')

    def test_none_dict_handling(self):
        """Test that None dictionary returns 'Unknown User'."""
        user_data = None
        result = get_user_identification(user_data)
        self.assertEqual(result, 'Unknown User')

    def test_missing_keys_handling(self):
        """Test that missing keys are handled gracefully."""
        user_data = {
            'some_other_field': 'value'
        }
        result = get_user_identification(user_data)
        self.assertEqual(result, 'Unknown User')


class TestCourseFlowInfo(unittest.TestCase):
    """Test cases for get_course_flow_info function."""

    def test_4th_stream_formatting(self):
        """Test formatting of 4th stream with Russian ordinal."""
        result = get_course_flow_info('4th_stream', '1 сентября')
        self.assertEqual(result, 'четвертый поток (старт 1 сентября)')

    def test_3rd_stream_formatting(self):
        """Test formatting of 3rd stream with Russian ordinal."""
        result = get_course_flow_info('3rd_stream', '15 августа')
        self.assertEqual(result, 'третий поток (старт 15 августа)')

    def test_2nd_stream_formatting(self):
        """Test formatting of 2nd stream with Russian ordinal."""
        result = get_course_flow_info('2nd_stream', '1 октября')
        self.assertEqual(result, 'второй поток (старт 1 октября)')

    def test_1st_stream_formatting(self):
        """Test formatting of 1st stream with Russian ordinal."""
        result = get_course_flow_info('1st_stream', '1 ноября')
        self.assertEqual(result, 'первый поток (старт 1 ноября)')

    def test_5th_stream_formatting(self):
        """Test formatting of 5th stream with Russian ordinal."""
        result = get_course_flow_info('5th_stream', '1 декабря')
        self.assertEqual(result, 'пятый поток (старт 1 декабря)')

    def test_10th_stream_formatting(self):
        """Test formatting of 10th stream with generic ordinal."""
        result = get_course_flow_info('10th_stream', '1 января')
        self.assertEqual(result, '10-й поток (старт 1 января)')

    def test_invalid_stream_format_fallback(self):
        """Test fallback formatting when stream format is invalid."""
        result = get_course_flow_info('invalid_stream', '1 февраля')
        self.assertEqual(result, 'invalid_stream (старт 1 февраля)')

    def test_missing_stream_parameter(self):
        """Test handling when course_stream is empty."""
        result = get_course_flow_info('', '1 марта')
        self.assertEqual(result, 'Информация о потоке недоступна')

    def test_missing_start_date_parameter(self):
        """Test handling when start_date_text is empty."""
        result = get_course_flow_info('4th_stream', '')
        self.assertEqual(result, 'Информация о потоке недоступна')

    def test_both_parameters_missing(self):
        """Test handling when both parameters are empty."""
        result = get_course_flow_info('', '')
        self.assertEqual(result, 'Информация о потоке недоступна')

    def test_none_parameters_handling(self):
        """Test handling when parameters are None."""
        result = get_course_flow_info(None, None)
        self.assertEqual(result, 'Информация о потоке недоступна')

    def test_mixed_none_empty_parameters(self):
        """Test handling when one parameter is None and other is empty."""
        result = get_course_flow_info('4th_stream', None)
        self.assertEqual(result, 'Информация о потоке недоступна')
        
        result = get_course_flow_info(None, '1 сентября')
        self.assertEqual(result, 'Информация о потоке недоступна')

    def test_custom_stream_format(self):
        """Test handling of custom stream formats."""
        result = get_course_flow_info('summer_stream', '1 июня')
        self.assertEqual(result, 'summer_stream (старт 1 июня)')

    def test_stream_with_numbers(self):
        """Test handling of stream names with numbers."""
        result = get_course_flow_info('stream_2024', '1 января')
        self.assertEqual(result, 'stream_2024 (старт 1 января)')


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
