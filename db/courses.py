"""
Course data access module.

This module provides functions to retrieve course information from hardcoded
constants instead of the database. Course data is defined in constants.py
and validated on first access to ensure data integrity.

The module maintains backward compatibility with the previous database-based
implementation, returning data in the same format expected by existing code.

Example usage:
    from db.courses import get_active_courses, get_course_by_id
    
    # Get all active courses
    active_courses = get_active_courses()
    for course in active_courses:
        print(f"{course['name']}: ${course['price_usd']}")
    
    # Get specific course
    course = get_course_by_id(1)
    if course:
        print(course['description'])
"""

import logging
import constants
from db.course_validation import (
    validate_all_courses,
    validate_course_id,
    log_validation_summary
)

# Configure logger
logger = logging.getLogger(__name__)

# Cache for validated courses
_validated_courses_cache = None


def _clear_validation_cache():
    """
    Clears the validated courses cache.
    
    This function is primarily used for testing to ensure each test
    starts with a fresh validation state. In production, the cache
    persists for the lifetime of the application.
    """
    global _validated_courses_cache
    _validated_courses_cache = None


def _get_validated_courses():
    """
    Gets validated courses from constants with caching.
    
    This internal function handles course validation and caching to ensure
    courses are only validated once per application lifecycle. If validation
    fails, it falls back to unvalidated data with a warning.
    
    Returns:
        list: List of validated course dictionaries with guaranteed structure:
            - id (int): Unique course identifier
            - name (str): Course display name
            - button_text (str): Text for selection button
            - description (str): Full course description
            - price_usd (int): Price in US dollars
            - price_usd_cents (int): Price in cents
            - is_active (bool): Whether course is available
            - start_date_text (str): Human-readable start date
    """
    global _validated_courses_cache
    
    if _validated_courses_cache is None:
        try:
            # Validate all courses on first access
            _validated_courses_cache = validate_all_courses(constants.COURSES)
            log_validation_summary(_validated_courses_cache)
        except ValueError as e:
            logger.error(f"Course validation failed: {str(e)}")
            # Fall back to unvalidated data if validation fails
            _validated_courses_cache = constants.COURSES
            logger.warning("Using unvalidated course data due to validation errors")
    
    return _validated_courses_cache


def get_active_courses():
    """
    Retrieves all active courses from constants.
    
    This function replaces the previous database query and returns courses
    where is_active=True. The data format matches the previous database
    implementation for backward compatibility.
    
    Returns:
        list: List of active course dictionaries, each containing:
            - id (int): Course ID
            - name (str): Course name
            - button_text (str): Button display text
            - description (str): Full description with formatting
            - price_usd (int): Price in dollars
            - price_usd_cents (int): Price in cents
            - is_active (bool): Always True for returned courses
            - start_date_text (str): Start date
            
    Example:
        >>> courses = get_active_courses()
        >>> for course in courses:
        ...     print(f"{course['name']}: ${course['price_usd']}")
        Вайб кодинг: $100
        Вайб кодинг EXTRA: $200
    """
    validated_courses = _get_validated_courses()
    return [course for course in validated_courses if course.get('is_active', True)]


def get_course_by_id(course_id):
    """
    Retrieves a specific course by its ID.
    
    This function replaces the previous database query and returns course
    data from constants. It accepts both integer and string IDs for
    backward compatibility.
    
    Args:
        course_id: Course identifier (int or str). String IDs are converted
                  to integers if possible. Invalid IDs return None.
    
    Returns:
        dict or None: Course dictionary if found, None otherwise.
                     Dictionary contains same fields as get_active_courses().
    
    Example:
        >>> course = get_course_by_id(1)
        >>> print(course['name'])
        Вайб кодинг
        
        >>> course = get_course_by_id("2")  # String ID also works
        >>> print(course['name'])
        Вайб кодинг EXTRA
        
        >>> course = get_course_by_id(999)  # Non-existent ID
        >>> print(course)
        None
    """
    # Validate course ID
    validated_id = validate_course_id(course_id)
    if validated_id is None:
        return None
    
    validated_courses = _get_validated_courses()
    for course in validated_courses:
        if course['id'] == validated_id:
            return course
    return None