"""
Course data validation module.

Provides validation functions for course data structures to ensure data integrity
and consistency. Includes field validation, logging of warnings, and default value
assignment for missing fields.
"""

import logging
from typing import Dict, List, Any, Optional

# Configure logger for course validation
logger = logging.getLogger(__name__)

# Required fields for course data
REQUIRED_FIELDS = {
    'id': int,
    'name': str,
    'button_text': str,
    'description': str,
    'price_usd': int,
}

# Optional fields with default values
OPTIONAL_FIELDS = {
    'price_usd_cents': lambda course: course.get('price_usd', 0) * 100,
    'is_active': True,
    'start_date_text': 'TBD',
}


def validate_course_structure(course: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and normalizes a single course data structure.
    
    Args:
        course: Dictionary containing course data
        
    Returns:
        Dictionary with validated and normalized course data
        
    Raises:
        ValueError: If required fields are missing or have invalid types
    """
    if not isinstance(course, dict):
        raise ValueError(f"Course data must be a dictionary, got {type(course).__name__}")
    
    validated_course = course.copy()
    
    # Validate required fields
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in course:
            raise ValueError(f"Required field '{field}' is missing from course data")
        
        value = course[field]
        if not isinstance(value, expected_type):
            raise ValueError(
                f"Field '{field}' must be of type {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
        
        # Additional validation for specific fields
        if field == 'id' and value <= 0:
            raise ValueError(f"Course ID must be positive, got {value}")
        
        if field in ['name', 'button_text', 'description'] and not value.strip():
            raise ValueError(f"Field '{field}' cannot be empty")
        
        if field == 'price_usd' and value < 0:
            raise ValueError(f"Price cannot be negative, got {value}")
    
    # Add optional fields with defaults if missing
    for field, default in OPTIONAL_FIELDS.items():
        if field not in validated_course:
            if callable(default):
                default_value = default(validated_course)
            else:
                default_value = default
            
            logger.warning(
                f"Optional field '{field}' missing from course ID {validated_course['id']}, "
                f"using default: {default_value}"
            )
            validated_course[field] = default_value
    
    # Validate data consistency
    if 'price_usd_cents' in validated_course:
        expected_cents = validated_course['price_usd'] * 100
        if validated_course['price_usd_cents'] != expected_cents:
            logger.warning(
                f"Price inconsistency in course ID {validated_course['id']}: "
                f"price_usd_cents ({validated_course['price_usd_cents']}) "
                f"doesn't match price_usd * 100 ({expected_cents})"
            )
            validated_course['price_usd_cents'] = expected_cents
    
    # Validate is_active field type
    if 'is_active' in validated_course and not isinstance(validated_course['is_active'], bool):
        logger.warning(
            f"Field 'is_active' in course ID {validated_course['id']} "
            f"should be boolean, got {type(validated_course['is_active']).__name__}"
        )
        validated_course['is_active'] = bool(validated_course['is_active'])
    
    return validated_course


def validate_all_courses(courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validates a list of course data structures.
    
    Args:
        courses: List of course dictionaries
        
    Returns:
        List of validated and normalized course dictionaries
        
    Raises:
        ValueError: If validation fails for any course
    """
    if not isinstance(courses, list):
        raise ValueError(f"Courses must be a list, got {type(courses).__name__}")
    
    validated_courses = []
    course_ids = set()
    
    for idx, course in enumerate(courses):
        try:
            validated_course = validate_course_structure(course)
            
            # Check for duplicate IDs
            course_id = validated_course['id']
            if course_id in course_ids:
                raise ValueError(f"Duplicate course ID: {course_id}")
            course_ids.add(course_id)
            
            validated_courses.append(validated_course)
            
        except ValueError as e:
            raise ValueError(f"Validation failed for course at index {idx}: {str(e)}")
    
    logger.info(f"Successfully validated {len(validated_courses)} courses")
    return validated_courses


def validate_course_id(course_id: Any) -> Optional[int]:
    """
    Validates and converts a course ID to integer.
    
    Args:
        course_id: The course ID to validate (can be int, str, or other)
        
    Returns:
        Integer course ID if valid, None otherwise
    """
    # Handle None explicitly
    if course_id is None:
        logger.warning("Course ID cannot be None")
        return None
    
    # Handle floats - reject them as invalid
    if isinstance(course_id, float):
        logger.warning(f"Course ID cannot be a float: {course_id}")
        return None
    
    try:
        # For strings, check if they would produce a float when converted
        if isinstance(course_id, str):
            # Strip whitespace
            course_id_stripped = course_id.strip()
            if not course_id_stripped:
                logger.warning("Course ID cannot be empty string")
                return None
            # Check for decimal point
            if '.' in course_id_stripped:
                logger.warning(f"Course ID cannot contain decimal point: {course_id}")
                return None
        
        # Convert to int if possible
        id_int = int(course_id)
        
        # Validate it's positive
        if id_int <= 0:
            logger.warning(f"Course ID must be positive, got {id_int}")
            return None
            
        return id_int
        
    except (ValueError, TypeError):
        logger.warning(f"Invalid course ID type: {type(course_id).__name__} with value {course_id}")
        return None


def log_validation_summary(courses: List[Dict[str, Any]]) -> None:
    """
    Logs a summary of course validation results.
    
    Args:
        courses: List of validated course dictionaries
    """
    total_courses = len(courses)
    active_courses = sum(1 for c in courses if c.get('is_active', True))
    inactive_courses = total_courses - active_courses
    
    logger.info(
        f"Course validation summary: "
        f"{total_courses} total courses, "
        f"{active_courses} active, "
        f"{inactive_courses} inactive"
    )
    
    # Log price range
    if courses:
        prices = [c['price_usd'] for c in courses]
        logger.info(
            f"Price range: ${min(prices)} - ${max(prices)} USD"
        )