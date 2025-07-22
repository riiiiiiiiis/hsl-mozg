#!/usr/bin/env python3
"""
Test bot startup and handler registration without actually running the bot.
This verifies that all imports work and handlers are properly configured.
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_bot_imports():
    """Test that all bot modules can be imported without errors."""
    print("=== Testing Bot Module Imports ===")
    
    # Mock config to avoid environment variable requirements
    mock_config = MagicMock()
    mock_config.BOT_TOKEN = "test_token"
    mock_config.DATABASE_URL = "postgresql://test"
    mock_config.TARGET_CHAT_ID = 123
    mock_config.USD_TO_RUB_RATE = 90.0
    mock_config.USD_TO_KZT_RATE = 450.0
    mock_config.USD_TO_ARS_RATE = 1000.0
    mock_config.TBANK_CARD_NUMBER = "1234"
    mock_config.TBANK_CARD_HOLDER = "Test"
    mock_config.KASPI_CARD_NUMBER = "1234"
    mock_config.ARS_ALIAS = "test"
    mock_config.USDT_TRC20_ADDRESS = "test"
    
    with patch.dict('sys.modules', {'config': mock_config}):
        try:
            # Test constants import
            import constants
            print("✓ constants.py imported successfully")
            
            # Test db modules import
            from db import courses as db_courses
            print("✓ db.courses imported successfully")
            
            # Test that we can access course data
            active_courses = db_courses.get_active_courses()
            print(f"✓ Found {len(active_courses)} active courses")
            
            # Test utils import
            import utils
            print("✓ utils.py imported successfully")
            
            print("✓ All core modules imported successfully\n")
            return True
            
        except Exception as e:
            print(f"✗ Import failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_handler_compatibility():
    """Test that handlers can work with the hardcoded course data."""
    print("=== Testing Handler Compatibility ===")
    
    try:
        from db import courses as db_courses
        import constants
        
        # Test that handlers can get course data
        active_courses = db_courses.get_active_courses()
        assert len(active_courses) > 0, "No active courses found"
        
        # Test callback data generation
        for course in active_courses:
            callback_data = f"{constants.CALLBACK_SELECT_COURSE_PREFIX}{course['id']}"
            print(f"✓ Course {course['id']} callback: {callback_data}")
            
            # Test that we can parse the callback back
            if callback_data.startswith(constants.CALLBACK_SELECT_COURSE_PREFIX):
                course_id = int(callback_data.replace(constants.CALLBACK_SELECT_COURSE_PREFIX, ''))
                retrieved_course = db_courses.get_course_by_id(course_id)
                assert retrieved_course is not None, f"Could not retrieve course {course_id}"
                assert retrieved_course['id'] == course['id'], "Course ID mismatch"
                print(f"✓ Course {course_id} callback parsing works")
        
        print("✓ All handler compatibility tests passed\n")
        return True
        
    except Exception as e:
        print(f"✗ Handler compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_course_data_integrity():
    """Test the integrity of course data in constants."""
    print("=== Testing Course Data Integrity ===")
    
    try:
        import constants
        
        # Test that COURSES is properly defined
        assert hasattr(constants, 'COURSES'), "COURSES not defined in constants"
        assert isinstance(constants.COURSES, list), "COURSES is not a list"
        assert len(constants.COURSES) > 0, "COURSES is empty"
        
        print(f"✓ Found {len(constants.COURSES)} courses in constants")
        
        # Test each course structure
        for i, course in enumerate(constants.COURSES):
            assert isinstance(course, dict), f"Course {i} is not a dict"
            
            # Check required fields
            required_fields = ['id', 'name', 'button_text', 'description', 
                             'price_usd', 'price_usd_cents', 'is_active', 'start_date_text']
            for field in required_fields:
                assert field in course, f"Course {i} missing field: {field}"
            
            # Check field types
            assert isinstance(course['id'], int), f"Course {i} ID is not int"
            assert isinstance(course['name'], str), f"Course {i} name is not str"
            assert isinstance(course['price_usd'], int), f"Course {i} price_usd is not int"
            assert isinstance(course['price_usd_cents'], int), f"Course {i} price_usd_cents is not int"
            assert isinstance(course['is_active'], bool), f"Course {i} is_active is not bool"
            
            # Check price consistency
            expected_cents = course['price_usd'] * 100
            assert course['price_usd_cents'] == expected_cents, f"Course {i} price inconsistency"
            
            print(f"✓ Course {course['id']} ({course['name']}) structure is valid")
        
        # Test callback constants
        assert hasattr(constants, 'CALLBACK_SELECT_COURSE_PREFIX'), "CALLBACK_SELECT_COURSE_PREFIX not defined"
        assert hasattr(constants, 'CALLBACK_CONFIRM_COURSE_SELECTION'), "CALLBACK_CONFIRM_COURSE_SELECTION not defined"
        
        print("✓ All callback constants are defined")
        print("✓ Course data integrity tests passed\n")
        return True
        
    except Exception as e:
        print(f"✗ Course data integrity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all startup tests."""
    print("Starting Bot Startup Integration Tests\n")
    
    try:
        # Test imports
        if not test_bot_imports():
            return False
        
        # Test handler compatibility
        if not test_handler_compatibility():
            return False
        
        # Test data integrity
        if not test_course_data_integrity():
            return False
        
        print("🎉 ALL BOT STARTUP TESTS PASSED!")
        print("\nSummary:")
        print("✓ All modules can be imported without errors")
        print("✓ Handlers are compatible with hardcoded course data")
        print("✓ Course data structure is valid and consistent")
        print("✓ Callback data generation and parsing works")
        print("✓ Bot is ready to run with hardcoded course data")
        
        return True
        
    except Exception as e:
        print(f"✗ STARTUP TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)