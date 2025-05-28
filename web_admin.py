#!/usr/bin/env python3
"""
Веб-интерфейс администратора на Flask
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import subprocess
import sys
import config

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def get_db_connection():
    """Создание подключения к базе данных"""
    conn = sqlite3.connect(config.DB_NAME)
    conn.row_factory = sqlite3.Row
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

if __name__ == '__main__':
    # Создаем папку для шаблонов если её нет
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("🚀 Запуск веб-интерфейса администратора...")
    print("📍 Откройте в браузере: http://localhost:5001")
    print("🛑 Для остановки нажмите Ctrl+C")
    
    app.run(debug=True, host='127.0.0.1', port=5001)