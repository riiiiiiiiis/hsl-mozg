#!/usr/bin/env python3
"""
Focused integration test for course info hardcoding feature.

This test verifies the key integration points:
1. /start command displays courses from constants
2. Course selection shows detailed information  
3. Booking process works with new course data
4. Price and description display correctly
"""

import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock config before importing other modules
mock_config = MagicMock()
mock_config.BOT_TOKEN = "test_token"
mock_config.DATABASE_URL = "postgresql://test"
mock_config.TARGET_CHAT_ID = 123
mock_config.USD_TO_RUB_RATE = 90.0
mock_config.USD_TO_KZT_RATE = 450.0
mock_config.USD_TO_ARS_RATE = 1000.0
mock_config.TBANK_CARD_NUMBER = "1234 5678 9012 3456"
mock_config.TBANK_CARD_HOLDER = "Test User"
mock_config.KASPI_CARD_NUMBER = "1234 5678 9012 3456"
mock_config.ARS_ALIAS = "test.alias"
mock_config.USDT_TRC20_ADDRESS = "TEST_USDT_ADDRESS"
mock_config.ADMIN_CONTACT = "@test_admin"

# Patch config module before importing handlers
sys.modules['config'] = mock_config

# Now import the handlers and other modules
from handlers.command_handlers import start_command
from handlers.callback_handlers import handle_select_course, handle_confirm_selection
import constants
from db import courses as db_courses


async def test_start_command():
    """Test /start command displays courses from constants."""
    print("Testing /start command...")
    
    # Mock database functions
    with patch('handlers.command_handlers.db_events.log_event'):
        # Create mock update and context
        mock_update = MagicMock()
        mock_context = MagicMock()
        
        # Setup mock user
        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.username = "testuser"
        mock_user.first_name = "Test User"
        
        # Setup mock message
        mock_message = MagicMock()
        mock_message.from_user = mock_user
        mock_message.reply_text = AsyncMock()
        
        mock_update.message = mock_message
        mock_context.args = []
        mock_context.user_data = {}
        
        # Execute start command
        await start_command(mock_update, mock_context)
        
        # Verify reply_text was called
        assert mock_message.reply_text.called, "reply_text was not called"
        
        # Get the call arguments
        call_args = mock_message.reply_text.call_args
        message_text = call_args[1]['text'] if 'text' in call_args[1] else call_args[0][0]
        reply_markup = call_args[1].get('reply_markup')
        
        # Verify message contains welcome text
        assert "Привет! Добро пожаловать в школу HashSlash!" in message_text
        assert "Выберите интересующий вас курс" in message_text
        
        # Verify reply markup contains course buttons
        assert reply_markup is not None, "No reply markup found"
        keyboard = reply_markup.inline_keyboard
        
        # Should have 2 buttons for 2 courses
        assert len(keyboard) == 2, f"Expected 2 course buttons, got {len(keyboard)}"
        
        # Check first course button
        first_button = keyboard[0][0]
        assert first_button.text == "Вайб Кодинг CORE - $100"
        assert first_button.callback_data == "select_course_1"
        
        # Check second course button
        second_button = keyboard[1][0]
        assert first_button.text == "Вайб Кодинг CORE - $100"
        assert second_button.callback_data == "select_course_2"
        
        print("✓ /start command displays courses correctly")


async def test_course_selection():
    """Test course selection shows detailed information."""
    print("Testing course selection...")
    
    with patch('handlers.callback_handlers.db_events.log_event'):
        # Create mock query and context
        mock_query = MagicMock()
        mock_context = MagicMock()
        
        # Setup mock user
        mock_user = MagicMock()
        mock_user.id = 12345
        
        mock_query.from_user = mock_user
        mock_query.data = "select_course_1"
        mock_query.answer = AsyncMock()
        mock_query.edit_message_text = AsyncMock()
        
        mock_context.user_data = {
            'user_id': 12345,
            'username': 'testuser',
            'first_name': 'Test User'
        }
        
        # Execute course selection handler directly
        await handle_select_course(mock_query, mock_context)
        
        # Verify edit_message_text was called
        assert mock_query.edit_message_text.called, "edit_message_text was not called"
        
        # Get the call arguments
        call_args = mock_query.edit_message_text.call_args
        message_text = call_args[0][0]
        reply_markup = call_args[1].get('reply_markup')
        
        # Debug: print the actual message text
        print(f"DEBUG: Actual message text: {repr(message_text)}")
        
        # Verify course details are displayed
        assert "Курс: Вайб кодинг" in message_text
        assert "Имя: Test User" in message_text
        assert "Старт: 23 июля" in message_text
        assert "Стоимость: <b>$100</b>" in message_text
        assert "ВТОРОЙ ПОТОК ВАЙБКОДИНГА" in message_text
        
        # Verify booking button is present
        assert reply_markup is not None, "No reply markup found"
        keyboard = reply_markup.inline_keyboard
        assert len(keyboard) == 1, "Expected 1 booking button"
        
        button = keyboard[0][0]
        assert button.text == "✅ Забронировать место"
        assert button.callback_data == "confirm_course_selection_v2"
        
        # Verify pending course ID is stored
        assert mock_context.user_data['pending_course_id'] == 1
        
        print("✓ Course selection shows details correctly")


async def test_booking_process():
    """Test booking process works with course data."""
    print("Testing booking process...")
    
    with patch('handlers.callback_handlers.db_events.log_event'), \
         patch('handlers.callback_handlers.db_bookings.create_booking') as mock_create_booking, \
         patch('handlers.callback_handlers.db_referrals.apply_referral_discount'):
        
        # Setup mock booking creation
        mock_create_booking.return_value = 12345
        
        # Create mock query and context
        mock_query = MagicMock()
        mock_context = MagicMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345
        
        mock_query.from_user = mock_user
        mock_query.answer = AsyncMock()
        mock_query.edit_message_text = AsyncMock()
        
        mock_context.user_data = {
            'user_id': 12345,
            'username': 'testuser',
            'first_name': 'Test User',
            'pending_course_id': 1  # CORE course
        }
        
        # Execute booking confirmation
        await handle_confirm_selection(mock_query, mock_context)
        
        # Verify booking was created with correct parameters
        mock_create_booking.assert_called_once_with(
            12345, 'testuser', 'Test User', 1, None, 0
        )
        
        # Get the booking message
        call_args = mock_query.edit_message_text.call_args
        message_text = call_args[0][0]
        
        # Verify course name and booking ID are in message
        assert "Вайб кодинг" in message_text
        assert "№*12345*" in message_text
        
        # Verify prices are calculated correctly for $100 course
        assert "9000\\.00 RUB" in message_text  # $100 * 90
        assert "45000\\.00 KZT" in message_text  # $100 * 450
        assert "100000\\.00 ARS" in message_text  # $100 * 1000
        assert "100\\.00 USDT" in message_text  # $100
        
        print("✓ Booking process works correctly")


def test_course_data_functions():
    """Test course data access functions."""
    print("Testing course data access functions...")
    
    # Test get_active_courses
    active_courses = db_courses.get_active_courses()
    assert len(active_courses) == 2, f"Expected 2 active courses, got {len(active_courses)}"
    
    for course in active_courses:
        assert course.get('is_active', True), f"Course {course['id']} is not active"
        assert 'id' in course, "Course missing 'id' field"
        assert 'name' in course, "Course missing 'name' field"
        assert 'price_usd' in course, "Course missing 'price_usd' field"
        assert 'price_usd_cents' in course, "Course missing 'price_usd_cents' field"
    
    # Test get_course_by_id
    course1 = db_courses.get_course_by_id(1)
    assert course1 is not None, "Course 1 not found"
    assert course1['name'] == "Вайб кодинг", f"Expected 'Вайб кодинг', got '{course1['name']}'"
    assert course1['price_usd'] == 100, f"Expected price 100, got {course1['price_usd']}"
    
    course2 = db_courses.get_course_by_id(2)
    assert course2 is not None, "Course 2 not found"
    assert course2['name'] == "Вайб кодинг EXTRA", f"Expected 'Вайб кодинг EXTRA', got '{course2['name']}'"
    assert course2['price_usd'] == 200, f"Expected price 200, got {course2['price_usd']}"
    
    # Test invalid course ID
    course_invalid = db_courses.get_course_by_id(999)
    assert course_invalid is None, "Invalid course ID should return None"
    
    print("✓ Course data access functions work correctly")


def test_price_consistency():
    """Test price consistency across the system."""
    print("Testing price consistency...")
    
    for course in constants.COURSES:
        # Check price_usd_cents = price_usd * 100
        expected_cents = course['price_usd'] * 100
        assert course['price_usd_cents'] == expected_cents, \
            f"Course {course['id']}: price_usd_cents ({course['price_usd_cents']}) != price_usd * 100 ({expected_cents})"
        
        # Check button text contains price
        price_str = f"${course['price_usd']}"
        assert price_str in course['button_text'], \
            f"Course {course['id']}: button_text doesn't contain price {price_str}"
        
        # Check description contains price
        assert price_str in course['description'], \
            f"Course {course['id']}: description doesn't contain price {price_str}"
    
    print("✓ Price consistency checks pass")


async def run_all_tests():
    """Run all integration tests."""
    print("🚀 Starting Focused Integration Tests")
    print("=" * 50)
    
    try:
        # Test course data access functions (synchronous)
        test_course_data_functions()
        test_price_consistency()
        
        # Test handler integration (asynchronous)
        await test_start_command()
        await test_course_selection()
        await test_booking_process()
        
        print("\n" + "=" * 50)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nThe course info hardcoding feature is working correctly:")
        print("✓ /start command displays courses from constants.py")
        print("✓ Course selection shows detailed information")
        print("✓ Booking process works with new course data")
        print("✓ Prices and descriptions display correctly")
        print("✓ Course data access functions work properly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)