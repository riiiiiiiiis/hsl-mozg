import os
import sys
import psycopg2

# Это нужно, чтобы скрипт мог найти ваш файл config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def main():
    """Добавляет начальный курс 'Вайб кодинг' в базу данных, если его там нет."""
    conn = None
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        print("Успешно подключились к базе данных.")
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к базе данных. Проверьте .env и запущен ли Docker. Ошибка: {e}")
        return
    
    # Полное описание курса
    full_description = "На этом курсе в течение двух недель я учу превращать идеи в рабочие прототипы. Программируем на русском языке. Наглядно объясняю как работает ИИ, интернет и приложения. Общение в закрытой группе, домашки, три созвона с записями. Поддержка продолжается месяц после курса.\nПосле обучения ты будешь знать как создавать сайты с помощью ИИ, что такое база данных, как собрать телеграм бота за вечер и выложить проект в интернет. Набор промптов в подарок!\nДля кого: вообще для всех\nДлительность: три недели\nФормат: 3 практических лекции по пятницам в 20:00 МСК в 20:00 МСК\nСтоимость: 150$\nСтарт: 30 мая\n\nОплата возможна переводом на карты Т-Банка, Каспи или в USDT на крипто кошелек.\n\nЧто дальше: После оплаты я добавлю тебя в закрытую группу, где мы будем общаться и делиться материалами. Перед стартом курса пришлю всю необходимую информацию."

    course_data = {
        "id": 1,
        "name": "Вайб кодинг",
        "description": full_description,
        "price_usd_cents": 15000,
        "button_text": "Вайб Кодинг",
        "is_active": True,
        "start_date_text": "30 мая"
    }

    try:
        with conn.cursor() as cur:
            # Сначала убедимся, что таблица courses существует
            cur.execute("SELECT to_regclass('public.courses');")
            if cur.fetchone()[0] is None:
                print("ОШИБКА: Таблица 'courses' не найдена. Запустите сначала 'python bot.py', чтобы он создал все таблицы.")
                return

            # Проверяем, есть ли уже курс с таким ID
            cur.execute("SELECT id FROM courses WHERE id = %s", (course_data['id'],))
            if cur.fetchone():
                print(f"Курс с ID {course_data['id']} ('{course_data['name']}') уже существует. Ничего не делаем.")
                return

            # Если курса нет, добавляем его
            print("Курс не найден, добавляем его в базу...")
            cur.execute("""
                INSERT INTO courses (id, name, description, price_usd_cents, button_text, is_active, start_date_text)
                VALUES (%(id)s, %(name)s, %(description)s, %(price_usd_cents)s, %(button_text)s, %(is_active)s, %(start_date_text)s)
            """, course_data)
            
            conn.commit()
            print("УСПЕХ! Начальный курс 'Вайб кодинг' добавлен в базу данных.")
            
    except Exception as e:
        print(f"Произошла ошибка при работе с базой данных: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()