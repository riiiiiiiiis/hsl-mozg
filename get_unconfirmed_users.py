#!/usr/bin/env python3
"""
Скрипт для получения списка участников, которые не подтвердили оплату.
Показывает участников со статусами: ожидает оплаты, загрузил чек (но не подтвержден), отменено.
"""

import sqlite3
from datetime import datetime, timedelta
import config

def get_db_connection():
    """Создание подключения к базе данных"""
    return sqlite3.connect(config.DB_NAME)

def get_unconfirmed_participants():
    """Получить список всех участников БЕЗ подтвержденной оплаты"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Запрос всех записей, где confirmed != 2 (не подтверждено)
    cursor.execute("""
        SELECT user_id, username, first_name, chosen_course, course_id, confirmed, created_at
        FROM bookings
        WHERE confirmed != 2
        ORDER BY created_at DESC
    """)
    
    participants = cursor.fetchall()
    conn.close()
    
    return participants

def display_unconfirmed_by_status():
    """Вывести список неподтвержденных участников, сгруппированных по статусу"""
    participants = get_unconfirmed_participants()
    
    if not participants:
        print("✅ Все участники подтвердили оплату!")
        return
    
    print(f"📋 Найдено участников БЕЗ подтвержденной оплаты: {len(participants)}\n")
    
    # Группировка по статусам
    statuses = {
        0: {"name": "🕐 Ожидают оплаты", "participants": []},
        1: {"name": "📸 Загрузили чек (ожидают проверки)", "participants": []},
        -1: {"name": "❌ Отменено", "participants": []}
    }
    
    for p in participants:
        status = p[5]  # confirmed field
        if status in statuses:
            statuses[status]["participants"].append(p)
    
    # Вывод по статусам
    for status_code, status_info in statuses.items():
        if status_info["participants"]:
            print(f"\n{status_info['name']}")
            print(f"Количество: {len(status_info['participants'])}")
            print("-" * 80)
            
            for idx, (user_id, username, first_name, chosen_course, course_id, confirmed, created_at) in enumerate(status_info['participants'], 1):
                # Вычисляем, сколько времени прошло с момента регистрации
                created_dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                time_passed = datetime.now() - created_dt
                days_passed = time_passed.days
                hours_passed = time_passed.seconds // 3600
                
                print(f"{idx}. User ID: {user_id}")
                print(f"   Имя: {first_name or 'Не указано'}")
                print(f"   Username: @{username if username else 'Не указан'}")
                print(f"   Курс: {chosen_course}")
                print(f"   Дата регистрации: {created_at}")
                print(f"   Прошло времени: {days_passed} дн. {hours_passed} ч.")
                
                # Особые пометки
                if status_code == 0 and days_passed > 1:
                    print(f"   ⚠️  Не оплатил более суток!")
                elif status_code == 1 and days_passed > 0:
                    print(f"   ⚠️  Чек ожидает проверки более {days_passed} дней!")
                
                print()

def get_statistics():
    """Получить общую статистику по всем бронированиям"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Общее количество бронирований
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total = cursor.fetchone()[0]
    
    # По статусам
    cursor.execute("SELECT confirmed, COUNT(*) FROM bookings GROUP BY confirmed")
    status_counts = cursor.fetchall()
    
    # По курсам
    cursor.execute("SELECT chosen_course, COUNT(*) FROM bookings GROUP BY chosen_course")
    course_counts = cursor.fetchall()
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("📊 ОБЩАЯ СТАТИСТИКА")
    print("=" * 80)
    print(f"\nВсего бронирований: {total}")
    
    print("\nПо статусам:")
    status_names = {0: "Ожидает оплаты", 1: "Загружен чек", 2: "Подтверждено", -1: "Отменено"}
    for status, count in status_counts:
        print(f"  {status_names.get(status, 'Неизвестно')}: {count}")
    
    print("\nПо курсам:")
    for course, count in course_counts:
        print(f"  {course}: {count}")

def get_pending_payment_ids():
    """Получить user_id тех, кто еще не оплатил (confirmed = 0)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, username, first_name, created_at
        FROM bookings
        WHERE confirmed = 0
        ORDER BY created_at DESC
    """)
    
    pending = cursor.fetchall()
    conn.close()
    
    if pending:
        print(f"\n💰 User IDs ожидающих оплаты ({len(pending)} чел.):")
        user_ids = [p[0] for p in pending]
        print(f"IDs: {user_ids}")
        
        # Показать тех, кто долго не платит
        print("\n⏰ Долго не оплачивают (более 24 часов):")
        old_pending = []
        for user_id, username, first_name, created_at in pending:
            created_dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            if datetime.now() - created_dt > timedelta(days=1):
                old_pending.append((user_id, username, first_name, created_at))
        
        if old_pending:
            for user_id, username, first_name, created_at in old_pending:
                print(f"  - {first_name or 'Без имени'} (@{username or 'без username'}) - ID: {user_id}, дата: {created_at}")
        else:
            print("  Нет")

if __name__ == "__main__":
    print("🔍 Поиск участников БЕЗ подтвержденной оплаты...\n")
    
    try:
        # Показать неподтвержденных по статусам
        display_unconfirmed_by_status()
        
        # Показать общую статистику
        get_statistics()
        
        # Показать ID для возможной рассылки напоминаний
        get_pending_payment_ids()
        
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")