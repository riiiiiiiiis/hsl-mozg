#!/usr/bin/env python3
"""
Веб-интерфейс администратора на Flask
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import subprocess
import sys
import random
import string
import config
import referral_config

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def get_db_connection():
    """Создание подключения к базе данных"""
    conn = sqlite3.connect(config.DB_NAME)
    conn.row_factory = sqlite3.Row
    
    # Создаем таблицы реферальной системы если их нет
    try:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {referral_config.REFERRAL_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT,
                discount_percent INTEGER NOT NULL,
                max_activations INTEGER NOT NULL,
                current_activations INTEGER DEFAULT 0,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {referral_config.REFERRAL_USAGE_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                booking_id INTEGER,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupon_id) REFERENCES {referral_config.REFERRAL_TABLE_NAME}(id),
                FOREIGN KEY (booking_id) REFERENCES bookings(id),
                UNIQUE(coupon_id, user_id)
            )
        """)
        
        # Проверяем и добавляем колонки в таблицу bookings если их нет
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'referral_code' not in columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN referral_code TEXT")
            print("Added referral_code column to bookings table")
        
        if 'discount_percent' not in columns:
            conn.execute("ALTER TABLE bookings ADD COLUMN discount_percent INTEGER DEFAULT 0")
            print("Added discount_percent column to bookings table")
        
        # Проверяем и добавляем колонку name в таблицу referral_coupons
        cursor.execute(f"PRAGMA table_info({referral_config.REFERRAL_TABLE_NAME})")
        ref_columns = [column[1] for column in cursor.fetchall()]
        
        if 'name' not in ref_columns:
            conn.execute(f"ALTER TABLE {referral_config.REFERRAL_TABLE_NAME} ADD COLUMN name TEXT")
            print("Added name column to referral_coupons table")
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating referral tables: {e}")
    
    return conn

@app.route('/')
def index():
    """Главная страница со статистикой"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute("SELECT COUNT(*) as total FROM bookings")
    total = cursor.fetchone()['total']
    
    # По статусам
    cursor.execute("""
        SELECT confirmed, COUNT(*) as count 
        FROM bookings 
        GROUP BY confirmed
    """)
    status_stats = cursor.fetchall()
    
    # По курсам
    cursor.execute("""
        SELECT chosen_course, COUNT(*) as count 
        FROM bookings 
        GROUP BY chosen_course
    """)
    course_stats = cursor.fetchall()
    
    # Последние регистрации
    cursor.execute("""
        SELECT username, first_name, chosen_course, confirmed, created_at 
        FROM bookings 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    recent_bookings = cursor.fetchall()
    
    conn.close()
    
    # Преобразуем статусы
    status_names = {
        '0': {'name': 'Ожидает оплаты', 'icon': '⏳', 'color': 'warning'},
        '1': {'name': 'Загружен чек', 'icon': '📸', 'color': 'info'},
        '2': {'name': 'Подтверждено', 'icon': '✅', 'color': 'success'},
        '-1': {'name': 'Отменено', 'icon': '❌', 'color': 'danger'}
    }
    
    status_data = []
    for stat in status_stats:
        status_info = status_names.get(str(stat['confirmed']), {
            'name': 'Неизвестно', 'icon': '❓', 'color': 'secondary'
        })
        status_data.append({
            'name': status_info['name'],
            'icon': status_info['icon'],
            'color': status_info['color'],
            'count': stat['count']
        })
    
    return render_template('index.html', 
                         total=total,
                         status_data=status_data,
                         course_stats=course_stats,
                         recent_bookings=recent_bookings,
                         status_names=status_names)

@app.route('/confirmed')
def confirmed_users():
    """Страница с подтвержденными участниками"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, username, first_name, chosen_course, created_at
        FROM bookings
        WHERE confirmed = 2
        ORDER BY chosen_course, created_at DESC
    """)
    
    participants = cursor.fetchall()
    conn.close()
    
    # Группировка по курсам
    courses = {}
    for p in participants:
        course = p['chosen_course']
        if course not in courses:
            courses[course] = []
        courses[course].append(p)
    
    # Список ID для рассылки
    user_ids = [p['user_id'] for p in participants]
    
    return render_template('confirmed.html', 
                         courses=courses,
                         total=len(participants),
                         user_ids=user_ids)

@app.route('/unconfirmed')
def unconfirmed_users():
    """Страница с неподтвержденными участниками"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, username, first_name, chosen_course, confirmed, created_at
        FROM bookings
        WHERE confirmed != 2
        ORDER BY confirmed, created_at DESC
    """)
    
    participants = cursor.fetchall()
    conn.close()
    
    # Группировка по статусам
    statuses = {
        0: {"name": "Ожидают оплаты", "icon": "🕐", "color": "warning", "participants": []},
        1: {"name": "Загрузили чек (ожидают проверки)", "icon": "📸", "color": "info", "participants": []},
        -1: {"name": "Отменено", "icon": "❌", "color": "danger", "participants": []}
    }
    
    for p in participants:
        status = p['confirmed']
        if status in statuses:
            # Вычисляем время
            created_dt = datetime.strptime(p['created_at'], "%Y-%m-%d %H:%M:%S")
            time_passed = datetime.now() - created_dt
            
            participant_data = dict(p)
            participant_data['days_passed'] = time_passed.days
            participant_data['hours_passed'] = time_passed.seconds // 3600
            participant_data['is_overdue'] = (status == 0 and time_passed.days > 1)
            
            statuses[status]["participants"].append(participant_data)
    
    return render_template('unconfirmed.html', statuses=statuses)

@app.route('/delete-test-users', methods=['POST'])
def delete_test_users():
    """Удаление тестовых записей"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Сначала проверяем количество
        cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE username = 'r1iiis'")
        count = cursor.fetchone()['count']
        
        if count > 0:
            cursor.execute("DELETE FROM bookings WHERE username = 'r1iiis'")
            conn.commit()
        
        conn.close()
        
        return jsonify({'success': True, 'deleted': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/prepare-messaging')
def prepare_messaging():
    """Подготовка рассылки"""
    try:
        # Запускаем скрипт рассылки
        result = subprocess.run([sys.executable, 'send_message_to_confirmed.py'], 
                              capture_output=True, text=True)
        
        return render_template('messaging.html', 
                             output=result.stdout,
                             error=result.stderr)
    except Exception as e:
        return render_template('messaging.html', 
                             output="",
                             error=str(e))

@app.route('/referrals')
def referrals():
    """Страница управления реферальными купонами"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем все купоны
    cursor.execute(f"""
        SELECT id, code, name, discount_percent, max_activations, current_activations, 
               created_at, is_active, created_by
        FROM {referral_config.REFERRAL_TABLE_NAME}
        ORDER BY created_at DESC
    """)
    coupons = cursor.fetchall()
    
    # Получаем статистику использования
    cursor.execute(f"""
        SELECT r.coupon_id, COUNT(*) as usage_count, MAX(r.used_at) as last_used
        FROM {referral_config.REFERRAL_USAGE_TABLE_NAME} r
        GROUP BY r.coupon_id
    """)
    usage_stats = {row['coupon_id']: row for row in cursor.fetchall()}
    
    conn.close()
    
    # Подготавливаем данные для отображения
    coupon_data = []
    for coupon in coupons:
        usage = usage_stats.get(coupon['id'], {})
        # Проверяем, является ли usage словарем или Row объектом
        if usage and not isinstance(usage, dict):
            last_used = usage['last_used'] if usage['last_used'] else 'Не использован'
        else:
            last_used = usage.get('last_used', 'Не использован') if isinstance(usage, dict) else 'Не использован'
            
        coupon_data.append({
            'id': coupon['id'],
            'code': coupon['code'],
            'name': coupon['name'] or '',
            'discount_percent': coupon['discount_percent'],
            'max_activations': coupon['max_activations'],
            'current_activations': coupon['current_activations'],
            'created_at': coupon['created_at'],
            'is_active': coupon['is_active'],
            'last_used': last_used,
            'remaining': coupon['max_activations'] - coupon['current_activations'],
            'is_expired': coupon['current_activations'] >= coupon['max_activations']
        })
    
    return render_template('referrals.html', 
                         coupons=coupon_data,
                         available_discounts=referral_config.REFERRAL_DISCOUNTS)

@app.route('/create-referral', methods=['POST'])
def create_referral():
    """Создание нового реферального купона"""
    try:
        discount_percent = int(request.form.get('discount_percent'))
        max_activations = int(request.form.get('max_activations'))
        name = request.form.get('name', '').strip()
        
        if discount_percent not in referral_config.REFERRAL_DISCOUNTS:
            return jsonify({'success': False, 'error': 'Недопустимый процент скидки'})
        
        if max_activations <= 0:
            return jsonify({'success': False, 'error': 'Количество активаций должно быть больше 0'})
        
        # Генерируем уникальный код
        code = ''.join(random.choices(referral_config.REFERRAL_CODE_CHARS, k=referral_config.REFERRAL_CODE_LENGTH))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            INSERT INTO {referral_config.REFERRAL_TABLE_NAME} 
            (code, name, discount_percent, max_activations, created_by) 
            VALUES (?, ?, ?, ?, ?)
        """, (code, name, discount_percent, max_activations, 0))  # 0 - ID админа из веб-панели
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'code': code,
            'name': name,
            'link': f"https://t.me/hashslash_bot?start={referral_config.REFERRAL_START_PARAMETER}{code}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/toggle-referral/<int:coupon_id>', methods=['POST'])
def toggle_referral(coupon_id):
    """Активация/деактивация купона"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE {referral_config.REFERRAL_TABLE_NAME}
            SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
            WHERE id = ?
        """, (coupon_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update-referral-name/<int:coupon_id>', methods=['POST'])
def update_referral_name(coupon_id):
    """Обновление имени купона"""
    try:
        name = request.form.get('name', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE {referral_config.REFERRAL_TABLE_NAME}
            SET name = ?
            WHERE id = ?
        """, (name, coupon_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update-referral-discount/<int:coupon_id>', methods=['POST'])
def update_referral_discount(coupon_id):
    """Обновление размера скидки купона"""
    try:
        discount_percent = int(request.form.get('discount_percent'))
        
        if discount_percent < 0 or discount_percent > 100:
            return jsonify({'success': False, 'error': 'Скидка должна быть от 0 до 100%'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE {referral_config.REFERRAL_TABLE_NAME}
            SET discount_percent = ?
            WHERE id = ?
        """, (discount_percent, coupon_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Создаем папку для шаблонов если её нет
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("🚀 Запуск веб-интерфейса администратора...")
    print("📍 Откройте в браузере: http://localhost:5001")
    print("🛑 Для остановки нажмите Ctrl+C")
    
    app.run(debug=True, host='127.0.0.1', port=5001)