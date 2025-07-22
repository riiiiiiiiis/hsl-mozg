"""
Unit tests for db/courses.py functions.

Tests the hardcoded course data functionality including:
- get_active_courses() with active course filtering
- get_course_by_id() with valid and invalid IDs
- Data format compatibility with existing code
- Edge case handling
"""

import unittest
from unittest.mock import patch
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.courses import get_active_courses, get_course_by_id, _clear_validation_cache
import constants


class TestCourses(unittest.TestCase):
    """Test cases for course data access functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Store original COURSES data to restore after tests
        self.original_courses = constants.COURSES.copy()
        # Clear validation cache before each test
        _clear_validation_cache()

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original COURSES data
        constants.COURSES = self.original_courses

    def test_get_active_courses_returns_all_active(self):
        """Test that get_active_courses() returns only active courses."""
        # Test with default data (all courses should be active)
        active_courses = get_active_courses()
        
        self.assertEqual(len(active_courses), 2)
        for course in active_courses:
            self.assertTrue(course.get('is_active', True))

    def test_get_active_courses_filters_inactive(self):
        """Test that get_active_courses() filters out inactive courses."""
        # Mock data with one inactive course
        test_courses = [
            {
                "id": 1,
                "name": "Active Course",
                "is_active": True,
                "price_usd": 100,
                "price_usd_cents": 10000,
                "button_text": "Active - $100",
                "start_date_text": "Today",
                "description": "Active course description"
            },
            {
                "id": 2,
                "name": "Inactive Course",
                "is_active": False,
                "price_usd": 200,
                "price_usd_cents": 20000,
                "button_text": "Inactive - $200",
                "start_date_text": "Tomorrow",
                "description": "Inactive course description"
            }
        ]
        
        with patch.object(constants, 'COURSES', test_courses):
            active_courses = get_active_courses()
            
            self.assertEqual(len(active_courses), 1)
            self.assertEqual(active_courses[0]['id'], 1)
            self.assertEqual(active_courses[0]['name'], "Active Course")

    def test_get_active_courses_handles_missing_is_active_field(self):
        """Test that courses without is_active field are treated as active."""
        test_courses = [
            {
                "id": 1,
                "name": "Course Without is_active",
                "price_usd": 100,
                "price_usd_cents": 10000,
                "button_text": "Course - $100",
                "start_date_text": "Today",
                "description": "Course description"
                # Note: no is_active field
            }
        ]
        
        with patch.object(constants, 'COURSES', test_courses):
            active_courses = get_active_courses()
            
            self.assertEqual(len(active_courses), 1)
            self.assertEqual(active_courses[0]['id'], 1)

    def test_get_course_by_id_valid_id(self):
        """Test get_course_by_id() with valid course IDs."""
        # Test with existing course ID
        course = get_course_by_id(1)
        
        self.assertIsNotNone(course)
        self.assertEqual(course['id'], 1)
        self.assertEqual(course['name'], "Вайб кодинг")
        self.assertEqual(course['price_usd'], 100)

        # Test with second course
        course = get_course_by_id(2)
        
        self.assertIsNotNone(course)
        self.assertEqual(course['id'], 2)
        self.assertEqual(course['name'], "Вайб кодинг EXTRA")
        self.assertEqual(course['price_usd'], 200)

    def test_get_course_by_id_invalid_id(self):
        """Test get_course_by_id() with invalid course IDs."""
        # Test with non-existent ID
        course = get_course_by_id(999)
        self.assertIsNone(course)

        # Test with negative ID
        course = get_course_by_id(-1)
        self.assertIsNone(course)

        # Test with zero ID
        course = get_course_by_id(0)
        self.assertIsNone(course)

    def test_get_course_by_id_string_id_conversion(self):
        """Test get_course_by_id() converts string IDs to integers."""
        # Test with string ID that can be converted
        course = get_course_by_id("1")
        
        self.assertIsNotNone(course)
        self.assertEqual(course['id'], 1)

        # Test with string ID for second course
        course = get_course_by_id("2")
        
        self.assertIsNotNone(course)
        self.assertEqual(course['id'], 2)

    def test_get_course_by_id_invalid_string_id(self):
        """Test get_course_by_id() handles invalid string IDs."""
        # Test with non-numeric string
        course = get_course_by_id("invalid")
        self.assertIsNone(course)

        # Test with empty string
        course = get_course_by_id("")
        self.assertIsNone(course)

        # Test with float string
        course = get_course_by_id("1.5")
        self.assertIsNone(course)

    def test_get_course_by_id_none_and_edge_cases(self):
        """Test get_course_by_id() handles None and other edge cases."""
        # Test with None
        course = get_course_by_id(None)
        self.assertIsNone(course)

        # Test with boolean False (int(False) = 0, which should not match any course)
        course = get_course_by_id(False)
        self.assertIsNone(course)

        # Test with list
        course = get_course_by_id([1])
        self.assertIsNone(course)

    def test_data_format_compatibility(self):
        """Test that returned data format is compatible with existing code."""
        # Test get_active_courses() returns list of dicts
        active_courses = get_active_courses()
        
        self.assertIsInstance(active_courses, list)
        for course in active_courses:
            self.assertIsInstance(course, dict)
            
            # Check all required fields are present
            required_fields = ['id', 'name', 'button_text', 'description', 
                             'price_usd', 'price_usd_cents', 'is_active', 'start_date_text']
            for field in required_fields:
                self.assertIn(field, course)

        # Test get_course_by_id() returns dict or None
        course = get_course_by_id(1)
        self.assertIsInstance(course, dict)
        
        # Check all required fields are present
        for field in required_fields:
            self.assertIn(field, course)

        # Test field types
        self.assertIsInstance(course['id'], int)
        self.assertIsInstance(course['name'], str)
        self.assertIsInstance(course['button_text'], str)
        self.assertIsInstance(course['description'], str)
        self.assertIsInstance(course['price_usd'], int)
        self.assertIsInstance(course['price_usd_cents'], int)
        self.assertIsInstance(course['is_active'], bool)
        self.assertIsInstance(course['start_date_text'], str)

    def test_course_data_consistency(self):
        """Test that course data is consistent and valid."""
        for course in constants.COURSES:
            # Test price consistency
            self.assertEqual(course['price_usd_cents'], course['price_usd'] * 100)
            
            # Test ID is positive integer
            self.assertIsInstance(course['id'], int)
            self.assertGreater(course['id'], 0)
            
            # Test required string fields are not empty
            self.assertTrue(course['name'].strip())
            self.assertTrue(course['button_text'].strip())
            self.assertTrue(course['description'].strip())
            self.assertTrue(course['start_date_text'].strip())

    def test_course_ids_are_unique(self):
        """Test that all course IDs are unique."""
        course_ids = [course['id'] for course in constants.COURSES]
        self.assertEqual(len(course_ids), len(set(course_ids)))

    def test_empty_courses_list(self):
        """Test behavior with empty courses list."""
        with patch.object(constants, 'COURSES', []):
            # Test get_active_courses with empty list
            active_courses = get_active_courses()
            self.assertEqual(len(active_courses), 0)
            
            # Test get_course_by_id with empty list
            course = get_course_by_id(1)
            self.assertIsNone(course)

    def test_course_button_text_contains_price(self):
        """Test that button text contains price information."""
        for course in constants.COURSES:
            button_text = course['button_text']
            price_str = f"${course['price_usd']}"
            self.assertIn(price_str, button_text)


if __name__ == '__main__':
    unittest.main()