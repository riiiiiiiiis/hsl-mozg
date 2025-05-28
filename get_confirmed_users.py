#!/usr/bin/env python3
"""
Скрипт для получения списка участников с подтвержденной оплатой.
Выводит информацию в консоль без отправки сообщений.
"""

import sqlite3
from datetime import datetime
import config

def get_db_connection():
    """Создание подключения к базе данных"""
    return sqlite3.connect(config.DB_NAME)

def get_confirmed_participants():
    """Получить список всех участников с подтвержденной оплатой (confirmed = 2)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Запрос всех записей с подтвержденной оплатой
    cursor.execute("""
        SELECT user_id, username, first_name, chosen_course, course_id, created_at
        FROM bookings
        WHERE confirmed = 2
        ORDER BY created_at DESC
    """)
    
    participants = cursor.fetchall()
    conn.close()
    
    return participants

def display_participants():
    """Вывести список участников в консоль"""
    participants = get_confirmed_participants()
    
    if not participants:
        print("❌ Нет участников с подтвержденной оплатой")
        return
    
    print(f"✅ Найдено участников с подтвержденной оплатой: {len(participants)}\n")
    print("-" * 80)
    
    # Группировка по курсам
    courses = {}
    for p in participants:
        course = p[3]  # chosen_course
        if course not in courses:
            courses[course] = []
        courses[course].append(p)
    
    # Вывод по курсам
    for course_name, course_participants in courses.items():
        print(f"\n📚 Курс: {course_name}")
        print(f"   Количество участников: {len(course_participants)}")
        print("-" * 80)
        
        for idx, (user_id, username, first_name, chosen_course, course_id, created_at) in enumerate(course_participants, 1):
            print(f"{idx}. User ID: {user_id}")
            print(f"   Имя: {first_name or 'Не указано'}")
            print(f"   Username: @{username if username else 'Не указан'}")
            print(f"   Дата регистрации: {created_at}")
            print(f"   ID курса: {course_id}")
            print()
    
    print("-" * 80)
    print(f"\n📊 Общая статистика:")
    print(f"   Всего подтвержденных участников: {len(participants)}")
    for course_name, course_participants in courses.items():
        print(f"   {course_name}: {len(course_participants)} чел.")

def get_user_ids_for_messaging():
    """Получить только user_id для будущей рассылки"""
    participants = get_confirmed_participants()
    user_ids = [p[0] for p in participants]
    
    print(f"\n💬 User IDs для рассылки сообщений:")
    print(f"Всего: {len(user_ids)} участников")
    print(f"IDs: {user_ids}")
    
    return user_ids

if __name__ == "__main__":
    print("🔍 Поиск участников с подтвержденной оплатой...\n")
    
    try:
        # Показать подробную информацию
        display_participants()
        
        # Показать список ID для рассылки
        user_ids = get_user_ids_for_messaging()
        
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")