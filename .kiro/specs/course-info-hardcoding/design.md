# Design Document

## Overview

Данный дизайн описывает перенос информации о курсах из базы данных PostgreSQL в код приложения. В настоящее время система использует таблицу `courses` для хранения информации о курсах, включая описания, цены и метаданные. Цель - заменить обращения к базе данных на использование статических данных в коде для упрощения управления контентом.

## Architecture

### Current Architecture
```
Command Handler -> db/courses.py -> PostgreSQL courses table -> Course Data
Callback Handler -> db/courses.py -> PostgreSQL courses table -> Course Data
```

### Target Architecture
```
Command Handler -> constants.py -> Hardcoded Course Data
Callback Handler -> constants.py -> Hardcoded Course Data
```

### Migration Strategy
1. Расширить существующую структуру `COURSES` в `constants.py`
2. Создать функции-адаптеры в `db/courses.py` для совместимости
3. Постепенно заменить прямые обращения к базе данных
4. Удалить неиспользуемые функции базы данных

## Components and Interfaces

### 1. Enhanced Course Data Structure (constants.py)

Текущая структура `COURSES` будет расширена для включения всех полей из базы данных:

```python
COURSES = [
    {
        "id": 1,  # Изменено с строки на число для совместимости
        "name": "Вайб кодинг",
        "button_text": "Вайб Кодинг CORE - $100",
        "description": "...",  # Полное описание курса
        "price_usd": 100,  # Существующее поле
        "price_usd_cents": 10000,  # Новое поле для совместимости с БД
        "is_active": True,  # Новое поле
        "start_date_text": "23 июля"  # Новое поле
    },
    # ... остальные курсы
]
```

### 2. Compatibility Layer (db/courses.py)

Функции `get_active_courses()` и `get_course_by_id()` будут переписаны для работы с данными из `constants.py`:

```python
def get_active_courses():
    """Returns active courses from constants instead of database."""
    return [course for course in constants.COURSES if course.get('is_active', True)]

def get_course_by_id(course_id):
    """Gets course by ID from constants instead of database."""
    for course in constants.COURSES:
        if course['id'] == int(course_id):
            return course
    return None
```

### 3. Data Format Compatibility

Для обеспечения совместимости с существующим кодом, данные из констант будут возвращаться в том же формате, что и из базы данных (dict-like объекты с доступом по ключам).

## Data Models

### Course Model Structure
```python
{
    "id": int,                    # Уникальный идентификатор курса
    "name": str,                  # Название курса
    "button_text": str,           # Текст для кнопки выбора курса
    "description": str,           # Полное описание курса с разметкой
    "price_usd": int,            # Цена в долларах (целое число)
    "price_usd_cents": int,      # Цена в центах для совместимости
    "is_active": bool,           # Флаг активности курса
    "start_date_text": str       # Текстовое представление даты старта
}
```

### Migration from Database Fields
- `id` (SERIAL) -> `id` (int)
- `name` (TEXT) -> `name` (str)  
- `button_text` (VARCHAR) -> `button_text` (str)
- `description` (TEXT) -> `description` (str)
- `price_usd_cents` (INTEGER) -> `price_usd_cents` (int)
- `is_active` (BOOLEAN) -> `is_active` (bool)
- `start_date_text` (VARCHAR) -> `start_date_text` (str)

## Error Handling

### Course Not Found
- Функция `get_course_by_id()` возвращает `None` если курс не найден
- Обработчики проверяют результат и показывают соответствующее сообщение

### Invalid Course ID
- Функция обрабатывает преобразование строки в число с помощью `int()`
- При ошибке преобразования возвращается `None`

### Data Consistency
- Все курсы должны иметь обязательные поля
- Валидация данных происходит на этапе разработки
- Отсутствующие поля получают значения по умолчанию

## Testing Strategy

### Unit Tests
1. **Test Course Data Access**
   - Тест получения активных курсов
   - Тест получения курса по ID
   - Тест обработки несуществующего ID

2. **Test Data Compatibility**
   - Проверка совместимости формата данных
   - Тест всех обязательных полей
   - Проверка типов данных

3. **Test Integration**
   - Тест работы с существующими обработчиками
   - Проверка отображения курсов в интерфейсе
   - Тест процесса бронирования

### Manual Testing
1. Проверка отображения списка курсов в `/start`
2. Проверка детального просмотра курса
3. Проверка процесса бронирования
4. Проверка корректности цен и описаний

## Implementation Considerations

### Backward Compatibility
- Сохранение существующих API функций
- Поддержка того же формата возвращаемых данных
- Минимальные изменения в обработчиках

### Performance Benefits
- Устранение запросов к базе данных для получения курсов
- Быстрый доступ к данным из памяти
- Уменьшение нагрузки на PostgreSQL

### Maintenance Benefits
- Простое редактирование описаний курсов в коде
- Версионирование изменений через Git
- Возможность использования IDE для редактирования

### Database Cleanup
- Таблица `courses` может быть помечена как deprecated
- Данные могут быть сохранены для истории
- Миграция может быть обратимой при необходимости