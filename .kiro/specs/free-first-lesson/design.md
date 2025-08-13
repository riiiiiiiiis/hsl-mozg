# Design Document

## Overview

Функциональность бесплатного первого урока будет интегрирована в существующую архитектуру Telegram бота HashSlash School. Система будет включать новую кнопку в главном меню, процесс регистрации с вводом email, хранение данных в базе данных и автоматическую отправку уведомлений с Google Meet ссылкой за 15 минут до начала урока.

## Architecture

### Database Layer
Будет создана только одна новая таблица `free_lesson_registrations` для хранения регистраций на бесплатный урок:

```sql
CREATE TABLE free_lesson_registrations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    email TEXT NOT NULL,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id)
);
```

Информация об уроке (название, описание, дата, время, ссылка) будет захардкожена в `constants.py`, аналогично тому, как сейчас хранится информация о курсах.

### Handler Integration
Новая функциональность будет интегрирована в существующую систему обработчиков:

1. **Command Handlers**: Модификация `start_command` для добавления кнопки бесплатного урока
2. **Callback Handlers**: Новые callback'и для обработки взаимодействия с бесплатным уроком
3. **Message Handlers**: Расширение для обработки ввода email в состоянии ожидания

### User State Management
Будет использована существующая система `context.user_data` для отслеживания состояния пользователя:
- `awaiting_free_lesson_email`: состояние ожидания ввода email для бесплатного урока

## Components and Interfaces

### 1. Database Module (`db/free_lessons.py`)

```python
def create_free_lesson_registration(user_id, username, first_name, email)
def get_registration_by_user(user_id)
def get_all_registrations_for_notification()
def mark_notification_sent(registration_id)
def is_user_registered(user_id)
```

### 2. Constants Extension (`constants.py`)

Добавление информации о бесплатном уроке:
```python
FREE_LESSON = {
    "title": "Бесплатный первый урок",
    "description": "Описание первого урока...",
    "date_text": "15 августа в 19:00 по МСК",
    "google_meet_link": "https://meet.google.com/xxx-xxxx-xxx",
    "is_active": True
}
```

### 2. Callback Handlers Extension

Новые callback префиксы в `constants.py`:
```python
CALLBACK_FREE_LESSON_INFO = "free_lesson_info"
CALLBACK_FREE_LESSON_REGISTER = "free_lesson_register"
```

Новые обработчики в `callback_handlers.py`:
```python
async def handle_free_lesson_info(query, context)
async def handle_free_lesson_register(query, context)
```

### 3. Message Handler Extension

Расширение `message_handlers.py` для обработки email:
```python
async def handle_email_input(update, context)
```

### 4. Notification System (`utils/notifications.py`)

```python
async def schedule_lesson_notifications(application)
async def send_lesson_reminders(application, lesson_config)
def validate_email(email_string)
```

## Data Models

### Free Lesson Registration
```python
{
    'id': int,
    'user_id': int,
    'username': str,
    'first_name': str,
    'email': str,
    'registered_at': datetime,
    'notification_sent': bool
}
```

### Free Lesson Config (Hardcoded in constants.py)
```python
FREE_LESSON = {
    'title': str,           # "Бесплатный первый урок"
    'description': str,     # Полное описание урока
    'date_text': str,       # "15 августа в 19:00 по МСК"
    'google_meet_link': str, # Ссылка на Google Meet
    'is_active': bool       # Активен ли урок для регистрации
}
```
```

## Error Handling

### Email Validation
- Проверка формата email с помощью регулярного выражения
- Обработка некорректного формата с повторным запросом
- Логирование попыток ввода неверного email

### Database Errors
- Обработка дублирующихся регистраций (UNIQUE constraint)
- Откат транзакций при ошибках
- Логирование всех database операций

### Notification Errors
- Обработка ошибок отправки сообщений
- Повторные попытки отправки при временных сбоях
- Логирование неудачных уведомлений

### State Management Errors
- Сброс состояния пользователя при ошибках
- Обработка некорректных переходов между состояниями
- Таймаут для состояния ожидания email (автосброс через 10 минут)

## Testing Strategy

### Unit Tests
1. **Database Operations**:
   - Тестирование создания регистрации
   - Тестирование валидации дублирующихся регистраций
   - Тестирование получения пользователей для уведомлений

2. **Email Validation**:
   - Тестирование корректных email форматов
   - Тестирование некорректных email форматов
   - Граничные случаи (пустые строки, специальные символы)

3. **State Management**:
   - Тестирование установки и сброса состояний
   - Тестирование переходов между состояниями

### Integration Tests
1. **End-to-End Registration Flow**:
   - Полный цикл от нажатия кнопки до сохранения в БД
   - Тестирование с различными пользователями
   - Тестирование повторных регистраций

2. **Notification System**:
   - Тестирование планирования уведомлений
   - Тестирование отправки уведомлений
   - Тестирование обработки ошибок уведомлений

### Manual Testing Scenarios
1. **User Experience Flow**:
   - Регистрация нового пользователя
   - Попытка повторной регистрации
   - Ввод некорректного email
   - Отмена процесса регистрации

2. **Admin Configuration**:
   - Обновление информации об уроке
   - Изменение даты и времени урока
   - Обновление Google Meet ссылки

## Implementation Notes

### Scheduling System
Для отправки уведомлений за 15 минут до урока будет использован простой подход:
- Дата и время урока захардкожены в `constants.py`
- Система периодически (каждую минуту) проверяет текущее время
- Когда до урока остается 15 минут, отправляются уведомления всем зарегистрированным пользователям
- Помечается флаг `notification_sent` для предотвращения повторных отправок

### Configuration Management
Информация об уроке (описание, дата, ссылка) захардкожена в `constants.py`. Для изменения нужно будет обновить код и перезапустить бота, аналогично тому, как сейчас обновляется информация о курсах.

### Internationalization Considerations
Все сообщения будут на русском языке, соответствуя текущему стилю бота. При необходимости в будущем можно добавить поддержку других языков.

### Security Considerations
- Email адреса будут валидироваться перед сохранением
- Google Meet ссылки будут проверяться на корректность формата
- Доступ к админским функциям будет ограничен через `REFERRAL_ADMIN_IDS`

### Performance Considerations
- Индексы на `user_id` и `lesson_date` для быстрого поиска
- Ограничение на количество регистраций на один урок (если необходимо)
- Оптимизация запросов для получения списка пользователей для уведомлений