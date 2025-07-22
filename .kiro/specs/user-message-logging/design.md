# Design Document

## Overview

Простое логирование текстовых сообщений пользователей в базу данных. Сохраняем сообщения на всякий случай, без дополнительной обработки.

## Architecture

Добавляем новую таблицу `user_messages` в существующую PostgreSQL базу и новый обработчик текстовых сообщений.

## Components and Interfaces

### Database Schema

```sql
CREATE TABLE user_messages (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Database Module: `db/user_messages.py`

```python
def log_user_message(user_id: int, message_text: str, username: str = None, first_name: str = None) -> bool
```
- Сохраняет сообщение в базу данных

### Message Handler: `handlers/message_handlers.py`

```python
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE)
```
- Получает текстовое сообщение и сохраняет его в базу

## Error Handling

Все ошибки логируются, но не влияют на работу бота. Если сохранение не удалось - ничего страшного, бот продолжает работать.