#!/usr/bin/env python3
"""
Скрипт для обновления данных пользователей в базе
"""

import sqlite3
import config

def get_db_connection():
    """Создание подключения к базе данных"""
    return sqlite3.connect(config.DB_NAME)

def update_users():
    """Обновить данные для @maskeliade и @doraxplorer"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Обновляем @maskeliade - меняем курс на "Вайб Кодинг" и статус на подтвержден
        print("Обновляю данные для @maskeliade...")
        cursor.execute("""
            UPDATE bookings 
            SET chosen_course = 'Вайб Кодинг', 
                course_id = '1',
                confirmed = 2
            WHERE username = 'maskeliade'
        """)
        maskeliade_updated = cursor.rowcount
        
        # Обновляем @doraxplorer - только статус на подтвержден
        print("Обновляю данные для @doraxplorer...")
        cursor.execute("""
            UPDATE bookings 
            SET confirmed = 2
            WHERE username = 'doraxplorer' AND chosen_course = 'Вайб Кодинг'
        """)
        doraxplorer_updated = cursor.rowcount
        
        # Проверяем результаты перед коммитом
        print("\n📋 Результаты обновления:")
        print(f"@maskeliade: обновлено {maskeliade_updated} записей")
        print(f"@doraxplorer: обновлено {doraxplorer_updated} записей")
        
        # Показываем обновленные данные
        cursor.execute("""
            SELECT username, first_name, chosen_course, confirmed, created_at
            FROM bookings
            WHERE username IN ('maskeliade', 'doraxplorer')
            ORDER BY username
        """)
        
        print("\n📊 Текущие данные пользователей:")
        for row in cursor.fetchall():
            username, first_name, chosen_course, confirmed, created_at = row
            status = {0: "Ожидает оплаты", 1: "Загружен чек", 2: "✅ Подтверждено", -1: "Отменено"}.get(confirmed, "Неизвестно")
            print(f"\n@{username}:")
            print(f"  Имя: {first_name or 'Не указано'}")
            print(f"  Курс: {chosen_course}")
            print(f"  Статус: {status}")
            print(f"  Дата: {created_at}")
        
        # Коммитим изменения
        conn.commit()
        print("\n✅ Изменения успешно сохранены!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Ошибка при обновлении: {e}")
    finally:
        conn.close()

def check_users_before():
    """Показать данные пользователей перед изменением"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("📋 Данные пользователей ДО изменения:")
    
    cursor.execute("""
        SELECT username, first_name, chosen_course, confirmed, created_at
        FROM bookings
        WHERE username IN ('maskeliade', 'doraxplorer')
        ORDER BY username
    """)
    
    users = cursor.fetchall()
    if not users:
        print("❌ Пользователи не найдены в базе")
        return False
    
    for row in users:
        username, first_name, chosen_course, confirmed, created_at = row
        status = {0: "Ожидает оплаты", 1: "Загружен чек", 2: "Подтверждено", -1: "Отменено"}.get(confirmed, "Неизвестно")
        print(f"\n@{username}:")
        print(f"  Имя: {first_name or 'Не указано'}")
        print(f"  Курс: {chosen_course}")
        print(f"  Статус: {status}")
        print(f"  Дата: {created_at}")
    
    conn.close()
    return True

if __name__ == "__main__":
    print("🔄 Обновление данных пользователей\n")
    print("=" * 60)
    
    # Показываем данные до изменения
    if check_users_before():
        print("\n" + "=" * 60)
        
        # Запрашиваем подтверждение
        print("\n⚠️  Будут выполнены следующие изменения:")
        print("1. @maskeliade - курс изменится на 'Вайб Кодинг', статус на 'Подтверждено'")
        print("2. @doraxplorer - статус изменится на 'Подтверждено'")
        
        confirmation = input("\nПродолжить? (да/yes для подтверждения): ").lower()
        
        if confirmation in ['да', 'yes', 'y', 'д']:
            print("\n" + "=" * 60)
            update_users()
        else:
            print("\n❌ Обновление отменено")