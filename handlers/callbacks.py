"""
Константы для callback данных
Все callback-related константы в одном месте
"""

# Callback префиксы для разных действий
CALLBACK_RESERVE_SPOT = "reserve_spot"
CALLBACK_SELECT_COURSE_PREFIX = "select_course_"
CALLBACK_CONFIRM_COURSE_SELECTION = "confirm_course_selection_v2"
CALLBACK_BACK_TO_COURSE_SELECTION = "back_to_course_selection"
CALLBACK_CANCEL_RESERVATION = "cancel_reservation"

# Админские callback
CALLBACK_ADMIN_APPROVE_PAYMENT = "admin_approve_"
CALLBACK_ADMIN_REJECT_PAYMENT = "admin_reject_"

# Callback для бесплатных уроков
CALLBACK_FREE_LESSON_PREFIX = "free_lesson_"
CALLBACK_FREE_LESSON_REGISTER_PREFIX = "free_lesson_register_"
CALLBACK_LESSON_LINK_PREFIX = "lesson_link_"