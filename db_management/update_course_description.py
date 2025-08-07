import os
import sys
import psycopg2

# Это нужно, чтобы скрипт мог найти ваш файл config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Получаем DATABASE_URL напрямую из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment variables")

def update_course_description(course_id, new_description):
    """Обновляет описание курса с правильным форматированием."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE courses SET description = %s WHERE id = %s",
                (new_description, course_id)
            )
            conn.commit()
            print(f"✅ Описание курса ID={course_id} успешно обновлено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# Корректное описание для курса CORE (ID=1)
core_description = """ТРЕТИЙ ПОТОК ВАЙБКОДИНГА

Научитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI

+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения

🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ

📚 ФОРМАТ:
• Видео-уроки + текстовые материалы
• 3 лайва с практикой
• Практические домашки с разбором
• Доступ к материалам навсегда

🛠 ИСПОЛЬЗУЕМ:
Последние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4
Вайбкодерские аппы: Cursor, Bolt, Gemini CLI, Claude Code

• Все материалы и записи
• Закрытый чат с поддержкой
• Обратная связь по домашкам

📅 Старт: 12 августа
⏰ Занятия по средам в 21:00 по мск

Оплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек."""

# Корректное описание для курса EXTRA (ID=2)
extra_description = """✌️ ВТОРОЙ ПОТОК ВАЙБКОДИНГА (РАСШИРЕННЫЙ)

"Я никогда не совалась в программирование. Курс открыл другой мир" — Радислава
"Навайбкодила мужу сайт" — Настя

Научитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI

+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения

🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ

📚 ФОРМАТ:
• Видео-уроки + текстовые материалы
• 3 лайва с практикой
• Практические домашки с разбором
• Доступ к материалам навсегда

🛠 ИСПОЛЬЗУЕМ:
Последние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4
Вайбкодерские аппы: Cursor, Windsurf, Bolt, Gemini CLI

⭐ EXTRA ($200):
• Всё из базового CORE +
• Доступ в личку на время курса
• Индивидуальное занятие после окончания

📅 Старт: 23 июля
⏰ Занятия по средам в 21:00 по мск

Оплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек."""

if __name__ == "__main__":
    print("Выберите курс для обновления:")
    print("1 - Вайб кодинг CORE")
    print("2 - Вайб кодинг EXTRA")
    
    choice = input("Введите номер (1 или 2): ").strip()
    
    if choice == "1":
        update_course_description(1, core_description)
    elif choice == "2":
        update_course_description(2, extra_description)
    else:
        print("❌ Неверный выбор. Введите 1 или 2.")