"""
Integration tests for course info hardcoding feature.

Tests the integration between handlers and the hardcoded course data:
- /start command displays courses from constants
- Course selection shows detailed information
- Booking process works with new course data
- Price and description display correctly
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handlers.command_handlers import start_command
from handlers.callback_handlers import handle_select_course, handle_confirm_selection
import constants
from db import courses as db_courses


class TestCourseIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration test cases for course hardcoding feature."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Store original COURSES data to restore after tests
        self.original_courses = constants.COURSES.copy()
        
        # Mock update and context objects
        self.mock_update = MagicMock()
        self.mock_context = MagicMock()
        self.mock_query = MagicMock()
        
        # Setup mock user
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.mock_user.username = "testuser"
        self.mock_user.first_name = "Test User"
        
        # Setup mock message
        self.mock_message = MagicMock()
        self.mock_message.from_user = self.mock_user
        self.mock_message.reply_text = AsyncMock()
        
        self.mock_update.message = self.mock_message
        self.mock_update.callback_query = self.mock_query
        
        # Setup mock query
        self.mock_query.from_user = self.mock_user
        self.mock_query.answer = AsyncMock()
        self.mock_query.edit_message_text = AsyncMock()
        
        # Setup mock context
        self.mock_context.args = []
        self.mock_context.user_data = {}

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original COURSES data
        constants.COURSES = self.original_courses

    @patch('handlers.command_handlers.db_events.log_event')
    async def test_start_command_displays_courses_from_constants(self, mock_log_event):
        """Test that /start command displays courses from constants.py."""
        # Execute start command
        await start_command(self.mock_update, self.mock_context)
        
        # Verify reply_text was called
        self.mock_message.reply_text.assert_called_once()
        
        # Get the call arguments
        call_args = self.mock_message.reply_text.call_args
        message_text = call_args[1]['text'] if 'text' in call_args[1] else call_args[0][0]
        reply_markup = call_args[1].get('reply_markup')
        
        # Verify message contains welcome text
        self.assertIn("Привет! Добро пожаловать в школу HashSlash!", message_text)
        self.assertIn("Выберите интересующий вас курс", message_text)
        
        # Verify reply markup contains course buttons
        self.assertIsNotNone(reply_markup)
        keyboard = reply_markup.inline_keyboard
        
        # Should have 2 buttons for 2 courses
        self.assertEqual(len(keyboard), 2)
        
        # Check first course button
        first_button = keyboard[0][0]
        self.assertEqual(first_button.text, "Вайб Кодинг CORE - $100")
        self.assertEqual(first_button.callback_data, "select_course_1")
        
        # Check second course button
        second_button = keyboard[1][0]
        self.assertEqual(second_button.text, "Вайб Кодинг EXTRA - $200")
        self.assertEqual(second_button.callback_data, "select_course_2")
        
        # Verify event logging
        mock_log_event.assert_called_once_with(
            12345, 'start_command',
            username='testuser',
            first_name='Test User'
        )

    @patch('handlers.command_handlers.db_events.log_event')
    async def test_start_command_with_inactive_courses(self, mock_log_event):
        """Test /start command when some courses are inactive."""
        # Mock data with one inactive course
        test_courses = [
            {
                "id": 1,
                "name": "Active Course",
                "button_text": "Active Course - $100",
                "is_active": True,
                "price_usd": 100,
                "price_usd_cents": 10000,
                "start_date_text": "Today",
                "description": "Active course description"
            },
            {
                "id": 2,
                "name": "Inactive Course", 
                "button_text": "Inactive Course - $200",
                "is_active": False,
                "price_usd": 200,
                "price_usd_cents": 20000,
                "start_date_text": "Tomorrow",
                "description": "Inactive course description"
            }
        ]
        
        with patch.object(constants, 'COURSES', test_courses):
            await start_command(self.mock_update, self.mock_context)
            
            # Get reply markup
            call_args = self.mock_message.reply_text.call_args
            reply_markup = call_args[1].get('reply_markup')
            
            # Should only have 1 button for active course
            keyboard = reply_markup.inline_keyboard
            self.assertEqual(len(keyboard), 1)
            
            # Check that only active course is shown
            button = keyboard[0][0]
            self.assertEqual(button.text, "Active Course - $100")
            self.assertEqual(button.callback_data, "select_course_1")

    @patch('handlers.callback_handlers.db_events.log_event')
    async def test_course_selection_shows_detailed_info(self, mock_log_event):
        """Test that course selection shows detailed course information."""
        # Setup callback data for first course
        self.mock_query.data = "select_course_1"
        self.mock_context.user_data = {
            'user_id': 12345,
            'username': 'testuser',
            'first_name': 'Test User'
        }
        
        # Execute course selection handler
        await handle_select_course(self.mock_query, self.mock_context)
        
        # Verify query answer was called
        self.mock_query.answer.assert_called_once()
        
        # Verify edit_message_text was called
        self.mock_query.edit_message_text.assert_called_once()
        
        # Get the call arguments
        call_args = self.mock_query.edit_message_text.call_args
        message_text = call_args[0][0]
        reply_markup = call_args[1].get('reply_markup')
        
        # Verify course details are displayed
        self.assertIn("Курс: Вайб кодинг", message_text)
        self.assertIn("Имя: Test User", message_text)
        self.assertIn("Старт: 23 июля", message_text)
        self.assertIn("Стоимость: <b>$100</b>", message_text)
        self.assertIn("ВТОРОЙ ПОТОК ВАЙБКОДИНГА", message_text)
        
        # Verify booking button is present
        self.assertIsNotNone(reply_markup)
        keyboard = reply_markup.inline_keyboard
        self.assertEqual(len(keyboard), 1)
        
        button = keyboard[0][0]
        self.assertEqual(button.text, "✅ Забронировать место")
        self.assertEqual(button.callback_data, "confirm_course_selection_v2")
        
        # Verify pending course ID is stored
        self.assertEqual(self.mock_context.user_data['pending_course_id'], 1)
        
        # Verify event logging
        mock_log_event.assert_called_once_with(
            12345, 'view_program',
            details={'course_id': 1},
            username='testuser',
            first_name='Test User'
        )

    @patch('handlers.callback_handlers.db_events.log_event')
    async def test_course_selection_with_referral_discount(self, mock_log_event):
        """Test course selection displays discounted price with referral."""
        # Setup callback data and referral info
        self.mock_query.data = "select_course_2"  # EXTRA course
        self.mock_context.user_data = {
            'user_id': 12345,
            'username': 'testuser',
            'first_name': 'Test User',
            'pending_referral_info': {
                'discount_percent': 20
            }
        }
        
        # Execute course selection handler
        await handle_select_course(self.mock_query, self.mock_context)
        
        # Get the message text
        call_args = self.mock_query.edit_message_text.call_args
        message_text = call_args[0][0]
        
        # Verify discounted price is displayed
        self.assertIn("Курс: Вайб кодинг EXTRA", message_text)
        self.assertIn("<s>$200</s> <b>$160</b> (скидка 20%)", message_text)

    async def test_course_selection_invalid_id(self):
        """Test course selection with invalid course ID."""
        # Setup callback data with invalid course ID
        self.mock_query.data = "select_course_999"
        self.mock_context.user_data = {
            'user_id': 12345,
            'username': 'testuser',
            'first_name': 'Test User'
        }
        
        # Execute course selection handler
        await handle_select_course(self.mock_query, self.mock_context)
        
        # Verify error message is displayed
        self.mock_query.edit_message_text.assert_called_once_with(
            "Извините, этот курс больше не доступен."
        )

    @patch('handlers.callback_handlers.db_bookings.create_booking')
    @patch('handlers.callback_handlers.db_events.log_event')
    @patch('config.USD_TO_RUB_RATE', 90.0)
    @patch('config.USD_TO_KZT_RATE', 450.0)
    @patch('config.USD_TO_ARS_RATE', 1000.0)
    async def test_booking_process_with_course_data(self, mock_log_event, mock_create_booking):
        """Test that booking process works with hardcoded course data."""
        # Setup mock booking creation
        mock_create_booking.return_value = 123
        
        # Setup context with course selection
        self.mock_context.user_data = {
            'user_id': 12345,
            'username': 'testuser',
            'first_name': 'Test User',
            'pending_course_id': 1  # CORE course
        }
        
        # Execute booking confirmation
        await handle_confirm_selection(self.mock_query, self.mock_context)
        
        # Verify booking was created with correct course ID
        mock_create_booking.assert_called_once_with(
            12345, 'testuser', 'Test User', 1, None, 0
        )
        
        # Get the booking message
        call_args = self.mock_query.edit_message_text.call_args
        message_text = call_args[0][0]
        
        # Verify course name and booking ID are in message
        self.assertIn("Вайб кодинг", message_text)
        self.assertIn("№*123*", message_text)
        
        # Verify prices are calculated correctly for $100 course
        self.assertIn("9000\\.00 RUB", message_text)  # $100 * 90
        self.assertIn("45000\\.00 KZT", message_text)  # $100 * 450
        self.assertIn("100000\\.00 ARS", message_text)  # $100 * 1000
        self.assertIn("100\\.00 USDT", message_text)  # $100

    @patch('handlers.callback_handlers.db_bookings.create_booking')
    @patch('handlers.callback_handlers.db_events.log_event')
    @patch('handlers.callback_handlers.db_referrals.apply_referral_discount')
    @patch('config.USD_TO_RUB_RATE', 90.0)
    async def test_booking_with_referral_discount(self, mock_apply_referral, mock_log_event, mock_create_booking):
        """Test booking process with referral discount applied."""
        # Setup mock booking creation
        mock_create_booking.return_value = 124
        
        # Setup context with course selection and referral
        self.mock_context.user_data = {
            'user_id': 12345,
            'username': 'testuser',
            'first_name': 'Test User',
            'pending_course_id': 2,  # EXTRA course ($200)
            'pending_referral_code': 'TEST20',
            'pending_referral_info': {
                'id': 1,
                'discount_percent': 20
            }
        }
        
        # Execute booking confirmation
        await handle_confirm_selection(self.mock_query, self.mock_context)
        
        # Verify booking was created with discount
        mock_create_booking.assert_called_once_with(
            12345, 'testuser', 'Test User', 2, 'TEST20', 20
        )
        
        # Verify referral discount was applied
        mock_apply_referral.assert_called_once_with(1, 12345, 124)
        
        # Get the booking message
        call_args = self.mock_query.edit_message_text.call_args
        message_text = call_args[0][0]
        
        # Verify discounted prices are shown ($200 * 0.8 = $160)
        self.assertIn("14400\\.00 RUB", message_text)  # $160 * 90
        self.assertIn("160\\.00 USDT", message_text)  # $160

    def test_get_active_courses_integration(self):
        """Test that get_active_courses works with current constants."""
        active_courses = db_courses.get_active_courses()
        
        # Should return both courses as they are active
        self.assertEqual(len(active_courses), 2)
        
        # Verify course data structure
        for course in active_courses:
            self.assertIn('id', course)
            self.assertIn('name', course)
            self.assertIn('button_text', course)
            self.assertIn('description', course)
            self.assertIn('price_usd', course)
            self.assertIn('price_usd_cents', course)
            self.assertIn('is_active', course)
            self.assertIn('start_date_text', course)
            
            # Verify is_active is True
            self.assertTrue(course['is_active'])

    def test_get_course_by_id_integration(self):
        """Test that get_course_by_id works with current constants."""
        # Test first course
        course1 = db_courses.get_course_by_id(1)
        self.assertIsNotNone(course1)
        self.assertEqual(course1['name'], "Вайб кодинг")
        self.assertEqual(course1['price_usd'], 100)
        self.assertEqual(course1['price_usd_cents'], 10000)
        
        # Test second course
        course2 = db_courses.get_course_by_id(2)
        self.assertIsNotNone(course2)
        self.assertEqual(course2['name'], "Вайб кодинг EXTRA")
        self.assertEqual(course2['price_usd'], 200)
        self.assertEqual(course2['price_usd_cents'], 20000)
        
        # Test non-existent course
        course_none = db_courses.get_course_by_id(999)
        self.assertIsNone(course_none)

    def test_price_consistency_in_constants(self):
        """Test that price fields are consistent in constants."""
        for course in constants.COURSES:
            # price_usd_cents should be price_usd * 100
            expected_cents = course['price_usd'] * 100
            self.assertEqual(course['price_usd_cents'], expected_cents)
            
            # Button text should contain price
            price_str = f"${course['price_usd']}"
            self.assertIn(price_str, course['button_text'])

    def test_course_descriptions_contain_expected_content(self):
        """Test that course descriptions contain expected marketing content."""
        for course in constants.COURSES:
            description = course['description']
            
            # Should contain key marketing elements
            self.assertIn("ВТОРОЙ ПОТОК ВАЙБКОДИНГА", description)
            self.assertIn("23 июля", description)  # Start date
            self.assertIn("AI", description)  # AI mention
            self.assertIn("программирование", description)  # Programming mention
            
            # Should contain price information
            price_str = f"${course['price_usd']}"
            self.assertIn(price_str, description)

    async def test_start_command_with_empty_courses(self):
        """Test /start command behavior when no courses are available."""
        with patch.object(constants, 'COURSES', []):
            await start_command(self.mock_update, self.mock_context)
            
            # Get the call arguments
            call_args = self.mock_message.reply_text.call_args
            message_text = call_args[1]['text'] if 'text' in call_args[1] else call_args[0][0]
            reply_markup = call_args[1].get('reply_markup')
            
            # Should show no courses message
            self.assertIn("К сожалению, сейчас нет доступных курсов", message_text)
            
            # Should have no reply markup
            self.assertIsNone(reply_markup)


if __name__ == '__main__':
    unittest.main()