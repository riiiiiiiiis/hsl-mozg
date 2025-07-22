"""
Unit tests for course data validation module.

Tests the validation functions including:
- Field validation for required and optional fields
- Type checking and data consistency
- Default value assignment
- Error handling for invalid data
- Logging of validation warnings
"""

import unittest
from unittest.mock import patch, MagicMock
import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.course_validation import (
    validate_course_structure,
    validate_all_courses,
    validate_course_id,
    log_validation_summary,
    REQUIRED_FIELDS,
    OPTIONAL_FIELDS
)


class TestCourseValidation(unittest.TestCase):
    """Test cases for course validation functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_course = {
            "id": 1,
            "name": "Test Course",
            "button_text": "Test - $100",
            "description": "Test description",
            "price_usd": 100,
            "price_usd_cents": 10000,
            "is_active": True,
            "start_date_text": "Today"
        }
        
        self.minimal_course = {
            "id": 2,
            "name": "Minimal Course",
            "button_text": "Minimal - $50",
            "description": "Minimal description",
            "price_usd": 50
        }

    def test_validate_course_structure_valid(self):
        """Test validation of a valid course structure."""
        result = validate_course_structure(self.valid_course)
        
        # Should return the same data
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], "Test Course")
        self.assertEqual(result['price_usd'], 100)
        self.assertEqual(result['price_usd_cents'], 10000)

    def test_validate_course_structure_minimal(self):
        """Test validation adds default values for optional fields."""
        with patch('db.course_validation.logger') as mock_logger:
            result = validate_course_structure(self.minimal_course)
            
            # Check defaults were added
            self.assertEqual(result['price_usd_cents'], 5000)  # 50 * 100
            self.assertEqual(result['is_active'], True)
            self.assertEqual(result['start_date_text'], 'TBD')
            
            # Check warnings were logged
            self.assertEqual(mock_logger.warning.call_count, 3)

    def test_validate_course_structure_missing_required(self):
        """Test validation fails for missing required fields."""
        incomplete_course = {
            "id": 1,
            "name": "Incomplete Course"
            # Missing button_text, description, price_usd
        }
        
        with self.assertRaises(ValueError) as context:
            validate_course_structure(incomplete_course)
        
        self.assertIn("Required field 'button_text' is missing", str(context.exception))

    def test_validate_course_structure_wrong_types(self):
        """Test validation fails for wrong field types."""
        wrong_type_course = {
            "id": "not_an_int",  # Should be int
            "name": "Test Course",
            "button_text": "Test",
            "description": "Test",
            "price_usd": 100
        }
        
        with self.assertRaises(ValueError) as context:
            validate_course_structure(wrong_type_course)
        
        self.assertIn("Field 'id' must be of type int", str(context.exception))

    def test_validate_course_structure_invalid_values(self):
        """Test validation fails for invalid field values."""
        # Test negative ID
        invalid_id_course = self.valid_course.copy()
        invalid_id_course['id'] = -1
        
        with self.assertRaises(ValueError) as context:
            validate_course_structure(invalid_id_course)
        self.assertIn("Course ID must be positive", str(context.exception))
        
        # Test empty name
        empty_name_course = self.valid_course.copy()
        empty_name_course['name'] = "   "
        
        with self.assertRaises(ValueError) as context:
            validate_course_structure(empty_name_course)
        self.assertIn("Field 'name' cannot be empty", str(context.exception))
        
        # Test negative price
        negative_price_course = self.valid_course.copy()
        negative_price_course['price_usd'] = -50
        
        with self.assertRaises(ValueError) as context:
            validate_course_structure(negative_price_course)
        self.assertIn("Price cannot be negative", str(context.exception))

    def test_validate_course_structure_price_consistency(self):
        """Test validation fixes price_usd_cents inconsistency."""
        inconsistent_course = self.valid_course.copy()
        inconsistent_course['price_usd_cents'] = 5000  # Should be 10000
        
        with patch('db.course_validation.logger') as mock_logger:
            result = validate_course_structure(inconsistent_course)
            
            # Should fix the inconsistency
            self.assertEqual(result['price_usd_cents'], 10000)
            
            # Should log warning
            mock_logger.warning.assert_called()
            args = mock_logger.warning.call_args[0][0]
            self.assertIn("Price inconsistency", args)

    def test_validate_course_structure_not_dict(self):
        """Test validation fails for non-dict input."""
        with self.assertRaises(ValueError) as context:
            validate_course_structure("not a dict")
        
        self.assertIn("Course data must be a dictionary", str(context.exception))

    def test_validate_all_courses_valid(self):
        """Test validation of multiple valid courses."""
        courses = [self.valid_course, self.minimal_course]
        
        with patch('db.course_validation.logger'):
            result = validate_all_courses(courses)
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['id'], 1)
            self.assertEqual(result[1]['id'], 2)
            # Minimal course should have defaults added
            self.assertEqual(result[1]['price_usd_cents'], 5000)

    def test_validate_all_courses_duplicate_ids(self):
        """Test validation fails for duplicate course IDs."""
        duplicate_courses = [
            self.valid_course,
            self.valid_course  # Same ID
        ]
        
        with self.assertRaises(ValueError) as context:
            validate_all_courses(duplicate_courses)
        
        self.assertIn("Duplicate course ID: 1", str(context.exception))

    def test_validate_all_courses_not_list(self):
        """Test validation fails for non-list input."""
        with self.assertRaises(ValueError) as context:
            validate_all_courses("not a list")
        
        self.assertIn("Courses must be a list", str(context.exception))

    def test_validate_all_courses_invalid_course(self):
        """Test validation fails if any course is invalid."""
        courses = [
            self.valid_course,
            {"id": 2}  # Missing required fields
        ]
        
        with self.assertRaises(ValueError) as context:
            validate_all_courses(courses)
        
        self.assertIn("Validation failed for course at index 1", str(context.exception))

    def test_validate_course_id_valid(self):
        """Test course ID validation with valid inputs."""
        # Integer ID
        self.assertEqual(validate_course_id(1), 1)
        self.assertEqual(validate_course_id(999), 999)
        
        # String ID that can be converted
        self.assertEqual(validate_course_id("42"), 42)
        self.assertEqual(validate_course_id(" 10 "), 10)

    def test_validate_course_id_invalid(self):
        """Test course ID validation with invalid inputs."""
        with patch('db.course_validation.logger'):
            # Non-positive IDs
            self.assertIsNone(validate_course_id(0))
            self.assertIsNone(validate_course_id(-5))
            
            # Invalid types
            self.assertIsNone(validate_course_id("abc"))
            self.assertIsNone(validate_course_id(None))
            self.assertIsNone(validate_course_id([1, 2]))
            self.assertIsNone(validate_course_id(3.14))
            self.assertIsNone(validate_course_id("1.5"))
            self.assertIsNone(validate_course_id(""))
            self.assertIsNone(validate_course_id("  "))

    def test_log_validation_summary(self):
        """Test validation summary logging."""
        courses = [
            {"id": 1, "price_usd": 100, "is_active": True},
            {"id": 2, "price_usd": 200, "is_active": False},
            {"id": 3, "price_usd": 150, "is_active": True}
        ]
        
        with patch('db.course_validation.logger') as mock_logger:
            log_validation_summary(courses)
            
            # Should log summary
            self.assertEqual(mock_logger.info.call_count, 2)
            
            # Check first info call (summary)
            summary_call = mock_logger.info.call_args_list[0][0][0]
            self.assertIn("3 total courses", summary_call)
            self.assertIn("2 active", summary_call)
            self.assertIn("1 inactive", summary_call)
            
            # Check second info call (price range)
            price_call = mock_logger.info.call_args_list[1][0][0]
            self.assertIn("$100 - $200", price_call)

    def test_boolean_coercion_for_is_active(self):
        """Test that non-boolean is_active values are coerced to boolean."""
        course = self.valid_course.copy()
        course['is_active'] = "yes"  # String instead of boolean
        
        with patch('db.course_validation.logger') as mock_logger:
            result = validate_course_structure(course)
            
            # Should convert to boolean
            self.assertIsInstance(result['is_active'], bool)
            self.assertEqual(result['is_active'], True)
            
            # Should log warning
            mock_logger.warning.assert_called()
            args = mock_logger.warning.call_args[0][0]
            self.assertIn("should be boolean", args)


if __name__ == '__main__':
    unittest.main()