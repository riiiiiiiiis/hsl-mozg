# Design Document

## Overview

Данный дизайн описывает обновление системы курсов и бесплатных уроков для нового потока, стартующего 1 сентября. Основные изменения включают обновление констант курсов, модификацию информации о бесплатном уроке и добавление системы типизации уроков для различения записавшихся пользователей.

## Architecture

### Current Architecture
- Информация о курсах хранится в константах `COURSES` в файле `constants.py`
- Информация о бесплатном уроке хранится в константе `FREE_LESSON`
- Регистрации на бесплатный урок сохраняются в таблице `free_lesson_registrations`
- Обработка регистраций происходит через модуль `db/free_lessons.py`

### Proposed Changes
1. **Обновление констант курсов**: Изменение дат и описаний в `COURSES` с маркировкой "4-й поток"
2. **Обновление информации о бесплатном уроке**: Замена контента в `FREE_LESSON`
3. **Добавление типизации уроков**: Новое поле `lesson_type` в таблице `free_lesson_registrations`
4. **Добавление маркировки потока курса**: Новое поле `course_stream` в таблице `bookings` для отслеживания потоков
5. **Миграция существующих данных**: Присвоение типа `vibecoding_lesson` существующим записям на бесплатный урок

## Components and Interfaces

### 1. Constants Update (`constants.py`)

#### Course Constants
```python
COURSES = [
    {
        "id": 1,
        "name": "Вайб кодинг",
        "button_text": "Вайб-кодинг: реализация продуктовых идей",
        "description": "✌️ ЧЕТВЕРТЫЙ ПОТОК ВАЙБКОДИНГА\n\n...",  # Updated content with 4th stream
        "price_usd": 150,
        "start_date_text": "1 сентября",  # Updated from "12 августа"
        # ... other fields
    },
    # Similar update for EXTRA course
]
```

#### Free Lesson Constants
```python
FREE_LESSON = {
    "title": "Вайбкодинг с Cursor",  # Updated title
    "button_text": "🆓 Вайбкодинг с Cursor",  # Updated button text
    "description": "🎯 ВАЙБКОДИНГ С CURSOR\n\n...",  # New description
    "date_text": "2 сентября в 21:00 по МСК",  # Updated date
    # ... other fields
}
```

### 2. Database Schema Changes

#### Table: `free_lesson_registrations`
Добавление нового поля для типизации уроков:

```sql
ALTER TABLE free_lesson_registrations 
ADD COLUMN lesson_type VARCHAR(50) DEFAULT 'cursor_lesson';
```

#### Table: `bookings`
Добавление нового поля для маркировки потока курса:

```sql
ALTER TABLE bookings 
ADD COLUMN course_stream VARCHAR(50) DEFAULT '4th_stream';
```

#### Lesson Types
- `vibecoding_lesson`: Пользователи, записавшиеся на предыдущие уроки вайбкодинга
- `cursor_lesson`: Пользователи, записавшиеся на новый урок "Вайбкодинг с Cursor"

### 3. Database Functions Update (`db/free_lessons.py`)

#### Modified Functions
1. **`create_free_lesson_registration()`**: Добавление параметра `lesson_type`
2. **`get_registrations_by_type()`**: Новая функция для фильтрации по типу урока
3. **`get_registration_stats()`**: Новая функция для статистики по типам уроков

#### New Function Signatures
```python
def create_free_lesson_registration(user_id, username, first_name, email, lesson_type='cursor_lesson'):
    """Creates a new free lesson registration with lesson type."""

def get_registrations_by_type(lesson_type):
    """Gets registrations filtered by lesson type."""

def get_registration_stats():
    """Gets registration statistics grouped by lesson type."""
```

## Data Models

### Course Data Structure
```python
{
    "id": int,                    # Unique identifier
    "name": str,                  # Course name
    "button_text": str,           # Button display text
    "description": str,           # Full course description
    "price_usd": int,            # Price in USD
    "price_usd_cents": int,      # Price in cents
    "is_active": bool,           # Availability status
    "start_date_text": str       # Human-readable start date
}
```

### Free Lesson Registration
```python
{
    "id": int,                    # Registration ID
    "user_id": int,              # Telegram user ID
    "username": str,             # Telegram username
    "first_name": str,           # User's first name
    "email": str,                # Email address
    "registered_at": datetime,   # Registration timestamp
    "notification_sent": bool,   # Notification status
    "lesson_type": str          # Type of lesson (new field)
}
```

## Error Handling

### Migration Errors
- **Database connection failures**: Retry mechanism with exponential backoff
- **Column addition failures**: Check if column already exists before adding
- **Data migration failures**: Log errors but continue with new registrations

### Validation Errors
- **Email validation**: Existing validation remains unchanged
- **Lesson type validation**: Validate against allowed types (`vibecoding_lesson`, `cursor_lesson`)
- **Course data validation**: Ensure all required fields are present in updated constants

### Rollback Strategy
- **Constants rollback**: Keep backup of original `constants.py`
- **Database rollback**: Create migration script to remove `lesson_type` column if needed
- **Data integrity**: Ensure existing functionality works even if migration partially fails

## Testing Strategy

### Unit Tests
1. **Constants validation**: Test updated course and free lesson constants
2. **Database functions**: Test new and modified functions in `db/free_lessons.py`
3. **Migration logic**: Test database schema changes and data migration
4. **Email validation**: Ensure existing validation still works

### Integration Tests
1. **Bot workflow**: Test complete user registration flow with new lesson type
2. **Admin interface**: Test statistics and filtering by lesson type
3. **Notification system**: Test that notifications work with new lesson data
4. **Course selection**: Test that updated course information displays correctly

### Test Data
```python
# Test courses with updated dates
TEST_COURSES = [
    {
        "id": 1,
        "name": "Test Вайб кодинг",
        "start_date_text": "1 сентября",
        # ... other test fields
    }
]

# Test free lesson with new format
TEST_FREE_LESSON = {
    "title": "Test Вайбкодинг с Cursor",
    "button_text": "🆓 Test Вайбкодинг с Cursor",
    # ... other test fields
}
```

### Migration Testing
1. **Schema migration**: Test adding `lesson_type` column
2. **Data migration**: Test updating existing records with `vibecoding_lesson` type
3. **New registrations**: Test that new registrations get `cursor_lesson` type
4. **Statistics**: Test that statistics correctly group by lesson type

## Implementation Phases

### Phase 1: Constants Update
- Update course descriptions and dates in `constants.py`
- Update free lesson information
- Test that bot displays new information correctly

### Phase 2: Database Schema Migration
- Add `lesson_type` column to `free_lesson_registrations` table
- Update existing records with `vibecoding_lesson` type
- Test database operations with new schema

### Phase 3: Code Updates
- Modify `db/free_lessons.py` functions to handle lesson types
- Add new functions for filtering and statistics
- Update bot handlers to use new lesson type system

### Phase 4: Testing and Validation
- Run comprehensive tests on updated system
- Validate that existing functionality still works
- Test new lesson type functionality

## Backward Compatibility

### Existing Data
- All existing registrations will be marked as `vibecoding_lesson`
- Existing functionality will continue to work without changes
- Statistics will show both vibecoding and cursor lesson registrations

### API Compatibility
- Existing database functions will maintain their signatures
- New optional parameters will have default values
- No breaking changes to existing bot workflows

## Performance Considerations

### Database Performance
- New `lesson_type` column is indexed for efficient filtering
- Migration script runs in batches to avoid long locks
- Statistics queries are optimized for lesson type grouping

### Memory Usage
- Updated constants don't significantly increase memory usage
- New database field adds minimal overhead
- Existing caching mechanisms remain effective