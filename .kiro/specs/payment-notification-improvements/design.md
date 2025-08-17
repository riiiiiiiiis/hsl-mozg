# Design Document

## Overview

This feature enhances the payment notification system by adding buyer identification information and preserving approved payment messages. The current system forwards payment receipts to an admin chat with basic information and uses `query.edit_message_text()` to replace the notification message with approval confirmation, effectively deleting the original content.

The enhancement will:
1. Include comprehensive buyer identification (username, name, or user ID) in payment notifications
2. Preserve approved payment messages by updating them instead of replacing them entirely
3. Maintain backward compatibility with the existing rejection workflow

## Architecture

The changes will be implemented in two main areas:

### 1. Message Handlers (`handlers/message_handlers.py`)
- **photo_handler()**: Modify admin notification message format to include buyer username/identification and course flow information
- **any_message_handler()**: Update admin notification format for alternative payment proofs with enhanced course details

### 2. Callback Handlers (`handlers/callback_handlers.py`)
- **handle_admin_approve()**: Change from `edit_message_text()` to `edit_message_reply_markup()` and append approval status to preserve original content

## Components and Interfaces

### User Identification Component
A utility function will be created to extract the best available user identification:

```python
def get_user_identification(user):
    """
    Returns the best available user identification string.
    Priority: username > full_name > user_id
    """
    if user.username:
        return f"@{user.username}"
    elif user.first_name or user.last_name:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        return full_name
    else:
        return f"ID: {user.id}"
```

### Course Flow Information Component
A utility function will extract course flow and start date information:

```python
def get_course_flow_info(course_name, start_date_text):
    """
    Returns formatted course flow information.
    For now, hardcoded as "4" based on current course description.
    """
    flow_number = "4"  # Extracted from course description or hardcoded
    return f"Поток: {flow_number} (старт: {start_date_text})"
```

### Message Format Updates
Current admin notification format:
```
🧾 Новый чек для проверки!
Пользователь: John (ID: 123456789)
Заявка №: 42
Курс: Вайб кодинг
```

Enhanced format:
```
🧾 Новый чек для проверки!
Пользователь: @johndoe (John, ID: 123456789)
Заявка №: 42
Курс: Вайб кодинг
Поток: 4 (старт: 1 сентября)
```

### Approval Message Preservation
Current behavior:
- Original message is completely replaced with: "✅ Оплата для заявки №42 (Пользователь 123456789) ПОДТВЕРЖДЕНА."

New behavior:
- Original message content is preserved
- Inline keyboard is removed
- Approval status is appended:
```
🧾 Новый чек для проверки!
Пользователь: @johndoe (John, ID: 123456789)
Заявка №: 42
Курс: Вайб кодинг
Поток: 4 (старт: 1 сентября)

✅ ОДОБРЕНО - 2024-08-17 15:30 UTC
```

## Data Models

No database schema changes are required. The enhancement uses existing data sources:

### Telegram User Properties:
- `user.username` (optional)
- `user.first_name` (optional)
- `user.last_name` (optional)
- `user.id` (always available)

### Course Information:
- Course flow number will be derived from course data or hardcoded based on current course configuration
- Start date is available from `course['start_date_text']` in the COURSES constant
- This information is accessible through the booking record's course_id

## Error Handling

### Missing User Information
- If username is None: fall back to full name
- If full name is None: fall back to user ID
- User ID is always available from Telegram API

### Message Update Failures
- If `edit_message_reply_markup()` fails: log error and fall back to current `edit_message_text()` behavior
- Preserve existing error handling for booking status updates

### Timezone Handling
- Use UTC for approval timestamps to ensure consistency
- Format: "YYYY-MM-DD HH:MM UTC"

## Testing Strategy

### Unit Tests
1. **User Identification Function**
   - Test with username present
   - Test with only first name
   - Test with first and last name
   - Test with only user ID

2. **Message Format Generation**
   - Test enhanced notification message format
   - Test approval status appending
   - Test with various user identification scenarios

### Integration Tests
1. **Payment Flow Testing**
   - Submit payment receipt and verify enhanced notification format
   - Approve payment and verify message preservation
   - Reject payment and verify existing behavior unchanged

2. **Edge Cases**
   - Test with users having no username
   - Test with users having special characters in names
   - Test message update failures

### Manual Testing
1. **Admin Workflow**
   - Verify username visibility in notifications
   - Verify ability to click on usernames for direct contact
   - Verify approved messages remain accessible in chat history
   - Verify rejection workflow remains unchanged

## Implementation Notes

### Backward Compatibility
- Rejection workflow remains unchanged (messages still deleted)
- All existing callback data formats preserved
- No changes to database structure or API contracts

### Performance Considerations
- User identification extraction is O(1) operation
- Message updates use existing Telegram Bot API methods
- No additional database queries required

### Security Considerations
- Username information is already available in forwarded messages
- No sensitive data exposure beyond current implementation
- Approval timestamps use UTC to prevent timezone-based information leakage