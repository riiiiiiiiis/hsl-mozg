import os
import sys
import psycopg2

# Это нужно, чтобы скрипт мог найти ваш файл config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def main():
    """Добавляет курсы 'Вайб кодинг' в базу данных."""
    conn = None
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        print("Успешно подключились к базе данных.")
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к базе данных. Проверьте .env и запущен ли Docker. Ошибка: {e}")
        return
    
    # Описания курсов
    core_description = "✌️ ВТОРОЙ ПОТОК ВАЙБКОДИНГА\n\n\"Я никогда не совалась в программирование. Курс открыл другой мир\" — Радислава\n\"Навайбкодила мужу сайт\" — Настя\n\nНаучитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI\n\n+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения\n\n🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ\n\n📚 ФОРМАТ:\n• Видео-уроки + текстовые материалы\n• 3 лайва с практикой\n• Практические домашки с разбором\n• Доступ к материалам навсегда\n\n🛠 ИСПОЛЬЗУЕМ:\nПоследние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4\nВайбкодерские аппы: Cursor, Windsurf, Bolt, Gemini CLI\n\n💰 CORE ($100):\n• Все материалы и записи\n• Закрытый чат с поддержкой\n• Обратная связь по домашкам\n\n📅 Старт: 23 июля\n⏰ Занятия по средам в 21:00 по мск\n\nОплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек."

    extra_description = "✌️ ВТОРОЙ ПОТОК ВАЙБКОДИНГА (РАСШИРЕННЫЙ)\n\n\"Я никогда не совалась в программирование. Курс открыл другой мир\" — Радислава\n\"Навайбкодила мужу сайт\" — Настя\n\nНаучитесь создавать сайты, веб-приложения и Telegram-ботов через диалог с AI\n\n+ освоите промпт-инжиниринг и поймёте как устроены современные AI и приложения\n\n🎯 БЕЗ НАВЫКОВ ПРОГРАММИРОВАНИЯ\n\n📚 ФОРМАТ:\n• Видео-уроки + текстовые материалы\n• 3 лайва с практикой\n• Практические домашки с разбором\n• Доступ к материалам навсегда\n\n🛠 ИСПОЛЬЗУЕМ:\nПоследние модели: OpenAI o3, Google Gemini 2.5 Pro, Anthropic Claude Sonnet 4\nВайбкодерские аппы: Cursor, Windsurf, Bolt, Gemini CLI\n\n⭐ EXTRA ($200):\n• Всё из базового CORE +\n• Доступ в личку на время курса\n• Индивидуальное занятие после окончания\n\n📅 Старт: 23 июля\n⏰ Занятия по средам в 21:00 по мск\n\nОплата возможна переводом на карты Т-Банка, Каспи, в песо или USDT на крипто кошелек."

    courses_data = [
        {
            "id": 1,
            "name": "Вайб кодинг",
            "description": core_description,
            "price_usd_cents": 10000,  # $100
            "button_text": "Вайб Кодинг CORE - $100",
            "is_active": True,
            "start_date_text": "23 июля"
        },
        {
            "id": 2,
            "name": "Вайб кодинг EXTRA",
            "description": extra_description,
            "price_usd_cents": 20000,  # $200
            "button_text": "Вайб Кодинг EXTRA - $200",
            "is_active": True,
            "start_date_text": "23 июля"
        }
    ]

    try:
        with conn.cursor() as cur:
            # Сначала убедимся, что таблица courses существует
            cur.execute("SELECT to_regclass('public.courses');")
            if cur.fetchone()[0] is None:
                print("ОШИБКА: Таблица 'courses' не найдена. Запустите сначала 'python bot.py', чтобы он создал все таблицы.")
                return

            # Обновляем или добавляем каждый курс
            for course_data in courses_data:
                # Проверяем, есть ли уже курс с таким ID
                cur.execute("SELECT id FROM courses WHERE id = %s", (course_data['id'],))
                existing_course = cur.fetchone()
                
                if existing_course:
                    print(f"Курс с ID {course_data['id']} уже существует. Обновляем...")
                    cur.execute("""
                        UPDATE courses 
                        SET name = %(name)s, description = %(description)s, price_usd_cents = %(price_usd_cents)s, 
                            button_text = %(button_text)s, is_active = %(is_active)s, start_date_text = %(start_date_text)s
                        WHERE id = %(id)s
                    """, course_data)
                    print(f"ОБНОВЛЁН курс '{course_data['name']}'")
                else:
                    # Если курса нет, добавляем его
                    print(f"Курс '{course_data['name']}' не найден, добавляем в базу...")
                    cur.execute("""
                        INSERT INTO courses (id, name, description, price_usd_cents, button_text, is_active, start_date_text)
                        VALUES (%(id)s, %(name)s, %(description)s, %(price_usd_cents)s, %(button_text)s, %(is_active)s, %(start_date_text)s)
                    """, course_data)
                    print(f"ДОБАВЛЕН курс '{course_data['name']}'")
            
            conn.commit()
            print("УСПЕХ! Все курсы обновлены в базе данных.")
            
    except Exception as e:
        print(f"Произошла ошибка при работе с базой данных: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()