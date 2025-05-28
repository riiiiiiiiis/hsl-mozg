#!/usr/bin/env python3
"""
Скрипт для удаления тестовых записей пользователя из базы данных
"""

import sqlite3
import config

def get_db_connection():
    """Создание подключения к базе данных"""
    return sqlite3.connect(config.DB_NAME)

def show_test_user_bookings():
    """Показать все записи тестового пользователя перед удалением"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Поиск записей по username (без @)
    cursor.execute("""
        SELECT id, user_id, username, first_name, chosen_course, confirmed, created_at
        FROM bookings
        WHERE username = 'r1iiis'
        ORDER BY created_at DESC
    """)
    
    bookings = cursor.fetchall()
    conn.close()
    
    if not bookings:
        print("❌ Записи пользователя @r1iiis не найдены")
        return []
    
    print(f"📋 Найдено записей пользователя @r1iiis: {len(bookings)}\n")
    for booking in bookings:
        id, user_id, username, first_name, chosen_course, confirmed, created_at = booking
        status = {0: "Ожидает оплаты", 1: "Загружен чек", 2: "Подтверждено", -1: "Отменено"}.get(confirmed, "Неизвестно")
        print(f"ID записи: {id}")
        print(f"  User ID: {user_id}")
        print(f"  Имя: {first_name}")
        print(f"  Курс: {chosen_course}")
        print(f"  Статус: {status}")
        print(f"  Дата: {created_at}")
        print("-" * 40)
    
    return bookings

def delete_test_user_bookings():
    """Удалить все записи тестового пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Удаление записей
        cursor.execute("""
            DELETE FROM bookings
            WHERE username = 'r1iiis'
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ Успешно удалено записей: {deleted_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Ошибка при удалении: {e}")
        return False
    finally:
        conn.close()
    
    return True

def main():
    print("🗑️  Удаление тестовых записей пользователя @r1iiis\n")
    print("=" * 60)
    
    # Показываем записи перед удалением
    bookings = show_test_user_bookings()
    
    if not bookings:
        return
    
    # Запрашиваем подтверждение
    print(f"\n⚠️  Будет удалено {len(bookings)} записей!")
    confirmation = input("Вы уверены? (да/yes для подтверждения): ").lower()
    
    if confirmation in ['да', 'yes', 'y', 'д']:
        if delete_test_user_bookings():
            print("\n🎉 Тестовые записи успешно удалены!")
            
            # Проверяем, что записи действительно удалены
            print("\n📋 Проверка после удаления:")
            show_test_user_bookings()
    else:
        print("\n❌ Удаление отменено")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹ Операция прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")