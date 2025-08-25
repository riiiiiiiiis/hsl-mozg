```
 ███╗   ███╗ ██████╗ ███████╗ ██████╗ 
 ████╗ ████║██╔═══██╗╚══███╔╝██╔════╝ 
 ██╔████╔██║██║   ██║  ███╔╝ ██║  ███╗
 ██║╚██╔╝██║██║   ██║ ███╔╝  ██║   ██║
 ██║ ╚═╝ ██║╚██████╔╝███████╗╚██████╔╝
 ╚═╝     ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝ 
  ╦ ╦┌─┐┌─┐┬ ┬╔═╗┬  ┌─┐┌─┐┬ ┬
  ╠═╣├─┤└─┐├─┤╚═╗│  ├─┤└─┐├─┤
  ╩ ╩┴ ┴└─┘┴ ┴╚═╝┴─┘┴ ┴└─┘┴ ┴
```

# HashSlash School Bot

Telegram-бот для школы программирования с системой курсов, бесплатных уроков, платежами и реферальной программой.

## Быстрый старт

```bash
git clone https://github.com/riiiiiiiiis/hsl-mozg.git
cd hsl-mozg
pip install -r requirements.txt
python bot.py
```

## Архитектура

### Структура проекта

```
hsl-mozg/
├── bot.py                     # Точка входа
├── config.py                  # Конфигурация через env переменные
├── constants.py               # УДАЛЕНО (устаревший)
│
├── data/                      # Данные в YAML
│   ├── courses.yaml           # Курсы
│   └── lessons.yaml           # Бесплатные уроки
│
├── locales/
│   └── ru.py                  # Тексты сообщений
│
├── utils/
│   ├── courses.py             # Загрузка курсов
│   ├── lessons.py             # Загрузка уроков
│   └── notifications.py       # Уведомления
│
├── handlers/
│   ├── callbacks.py           # Callback константы
│   ├── command_handlers.py    # Команды
│   ├── callback_handlers.py   # Inline кнопки
│   └── message_handlers.py    # Сообщения
│
└── db/
    ├── base.py               # Подключение к PostgreSQL
    ├── bookings.py           # Брони
    ├── courses.py            # Курсы
    ├── events.py             # Аналитика
    ├── referrals.py          # Рефералы
    └── free_lessons.py       # Бесплатные уроки
```

### Принципы

- Разделение ответственности - каждый модуль за свое
- Контент отделен от кода - YAML файлы
- Все настройки через переменные окружения
- Кэширование данных для производительности

## Конфигурация

Обязательные переменные окружения:

```env
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql://user:pass@host:port/db
TARGET_CHAT_ID=admin_chat_id

# Платежи
TBANK_CARD_NUMBER=1234 5678 9012 3456
TBANK_CARD_HOLDER=Name Surname
KASPI_CARD_NUMBER=1234 5678 9012 3456
ARS_ALIAS=your.alias
USDT_TRC20_ADDRESS=your_address

# Курсы валют
USD_TO_RUB_RATE=95.0
USD_TO_KZT_RATE=470.0
USD_TO_ARS_RATE=1000.0
```

## Управление контентом

### Курсы (data/courses.yaml)

```yaml
courses:
  - id: 1
    name: "Вайб кодинг"
    button_text: "Полный курс"
    description: "Описание курса..."
    price_usd: 150
    is_active: true
    start_date_text: "1 сентября"
```

### Уроки (data/lessons.yaml)

```yaml
lessons:
  cursor_lesson:
    id: 1
    title: "Урок по Cursor"
    button_text: "🆓 Бесплатный урок"
    description: "Описание урока..."
    datetime: "2025-09-02T21:00:00"
    is_active: true
    reminder_text: "Напоминание..."
```

### Тексты (locales/ru.py)

```python
FREE_LESSON = {
    "EMAIL_REQUEST": "Введите email:",
    "REGISTRATION_SUCCESS": "Вы записаны!",
}

def get_text(category, key, **kwargs):
    # Функция для получения текстов с форматированием
```

## Команды

**Пользователи:**
- `/start` - Главное меню
- `/start ref_CODE` - Активация реферального кода
- `/reset` - Сброс сессии

**Админы:**
- `/create_referral [процент] [активации]` - Создать купон
- `/referral_stats` - Статистика купонов
- `/stats` - Общая статистика

## База данных

**Таблицы:**
- `bookings` - Брони курсов
- `<REFERRAL_TABLE_NAME>` - Реферальные купоны (см. config)
- `<REFERRAL_USAGE_TABLE_NAME>` - История использования (см. config)
- `events` - Аналитика
- `free_lesson_registrations` - Регистрации на уроки

## Основные процессы

**Регистрация на курс:**
1. Выбор курса
2. Применение скидки (если есть)
3. Бронь на 1 час
4. Загрузка чека
5. Модерация админом
6. Подтверждение

**Бесплатные уроки:**
1. Выбор урока
2. Ввод email
3. Уведомление за 15 минут
4. Ссылка на видеовстречу

## Деплой

**Railway:**
- Подключить репозиторий
- Установить env переменные
- Procfile: `worker: python bot.py`

**Локально:**
```bash
docker-compose up -d  # PostgreSQL
pip install -r requirements.txt
python bot.py
```

## Технический стек

- Python 3.11+
- python-telegram-bot 20+
- PostgreSQL
- PyYAML
- asyncio

## Безопасность

- Секреты в переменных окружения
- Проверка прав администратора
- Параметризованные SQL запросы
- Валидация ввода
- Экранирование текста

---

**HashSlash School** - AI-программирование