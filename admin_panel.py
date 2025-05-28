#!/usr/bin/env python3
"""
Визуальный интерфейс администратора для управления участниками курсов
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
from datetime import datetime, timedelta
import subprocess
import sys
import config

class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Панель администратора - HashSlash School")
        self.root.geometry("900x700")
        
        # Создаем стиль
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основной контейнер
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="🎓 Панель управления участниками", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Кнопки действий
        self.create_buttons(main_frame)
        
        # Текстовое поле для вывода
        self.create_output_area(main_frame)
        
        # Статус бар
        self.create_status_bar(main_frame)
        
        # Настройка размеров
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # При запуске показываем статистику
        self.show_statistics()
    
    def create_buttons(self, parent):
        """Создание кнопок управления"""
        # Фрейм для кнопок
        button_frame = ttk.LabelFrame(parent, text="Действия", padding="10")
        button_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Кнопки просмотра
        ttk.Button(button_frame, text="📊 Общая статистика", 
                  command=self.show_statistics, width=25).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(button_frame, text="✅ Подтвержденные участники", 
                  command=self.show_confirmed, width=25).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(button_frame, text="⏳ Неподтвержденные участники", 
                  command=self.show_unconfirmed, width=25).grid(row=0, column=2, padx=5, pady=5)
        
        # Кнопки действий
        ttk.Button(button_frame, text="💬 Подготовить рассылку", 
                  command=self.prepare_messaging, width=25).grid(row=1, column=0, padx=5, pady=5)
        
        ttk.Button(button_frame, text="🗑️ Удалить тестовые записи", 
                  command=self.delete_test_records, width=25).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(button_frame, text="🔄 Обновить данные", 
                  command=self.refresh_data, width=25).grid(row=1, column=2, padx=5, pady=5)
    
    def create_output_area(self, parent):
        """Создание области вывода"""
        output_frame = ttk.LabelFrame(parent, text="Информация", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Текстовое поле с прокруткой
        self.output_text = scrolledtext.ScrolledText(output_frame, height=20, width=80, 
                                                     font=('Courier', 10))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка тегов для форматирования
        self.output_text.tag_configure("header", font=('Courier', 12, 'bold'))
        self.output_text.tag_configure("success", foreground="green")
        self.output_text.tag_configure("error", foreground="red")
        self.output_text.tag_configure("warning", foreground="orange")
        self.output_text.tag_configure("info", foreground="blue")
    
    def create_status_bar(self, parent):
        """Создание статус бара"""
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
    
    def clear_output(self):
        """Очистка области вывода"""
        self.output_text.delete(1.0, tk.END)
    
    def write_output(self, text, tag=None):
        """Вывод текста в область вывода"""
        self.output_text.insert(tk.END, text, tag)
        self.output_text.see(tk.END)
        self.root.update()
    
    def get_db_connection(self):
        """Создание подключения к базе данных"""
        return sqlite3.connect(config.DB_NAME)
    
    def show_statistics(self):
        """Показать общую статистику"""
        self.clear_output()
        self.status_var.set("Загрузка статистики...")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Заголовок
            self.write_output("📊 ОБЩАЯ СТАТИСТИКА\n", "header")
            self.write_output("=" * 70 + "\n\n")
            
            # Общее количество
            cursor.execute("SELECT COUNT(*) FROM bookings")
            total = cursor.fetchone()[0]
            self.write_output(f"Всего бронирований: {total}\n\n")
            
            # По статусам
            self.write_output("По статусам:\n", "info")
            cursor.execute("SELECT confirmed, COUNT(*) FROM bookings GROUP BY confirmed")
            status_counts = cursor.fetchall()
            
            status_names = {0: "⏳ Ожидает оплаты", 1: "📸 Загружен чек", 
                          2: "✅ Подтверждено", -1: "❌ Отменено"}
            
            for status, count in status_counts:
                name = status_names.get(status, "Неизвестно")
                self.write_output(f"  {name}: {count}\n")
            
            # По курсам
            self.write_output("\nПо курсам:\n", "info")
            cursor.execute("SELECT chosen_course, COUNT(*) FROM bookings GROUP BY chosen_course")
            course_counts = cursor.fetchall()
            
            for course, count in course_counts:
                self.write_output(f"  📚 {course}: {count} чел.\n")
            
            # Последние регистрации
            self.write_output("\nПоследние 5 регистраций:\n", "info")
            cursor.execute("""
                SELECT username, first_name, chosen_course, confirmed, created_at 
                FROM bookings 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            recent = cursor.fetchall()
            for i, (username, first_name, course, status, created_at) in enumerate(recent, 1):
                status_icon = {0: "⏳", 1: "📸", 2: "✅", -1: "❌"}.get(status, "?")
                self.write_output(f"\n{i}. {first_name or 'Без имени'} (@{username or 'без username'})\n")
                self.write_output(f"   Курс: {course}\n")
                self.write_output(f"   Статус: {status_icon}\n")
                self.write_output(f"   Дата: {created_at}\n")
            
            conn.close()
            self.status_var.set("Статистика загружена")
            
        except Exception as e:
            self.write_output(f"\nОшибка: {str(e)}\n", "error")
            self.status_var.set("Ошибка при загрузке данных")
    
    def show_confirmed(self):
        """Показать подтвержденных участников"""
        self.clear_output()
        self.status_var.set("Загрузка подтвержденных участников...")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, first_name, chosen_course, created_at
                FROM bookings
                WHERE confirmed = 2
                ORDER BY chosen_course, created_at DESC
            """)
            
            participants = cursor.fetchall()
            conn.close()
            
            self.write_output("✅ ПОДТВЕРЖДЕННЫЕ УЧАСТНИКИ\n", "header")
            self.write_output("=" * 70 + "\n\n")
            
            if not participants:
                self.write_output("Нет подтвержденных участников\n", "warning")
            else:
                self.write_output(f"Всего: {len(participants)} человек\n\n", "success")
                
                # Группировка по курсам
                courses = {}
                for p in participants:
                    course = p[3]
                    if course not in courses:
                        courses[course] = []
                    courses[course].append(p)
                
                for course_name, course_participants in courses.items():
                    self.write_output(f"\n📚 {course_name} ({len(course_participants)} чел.)\n", "info")
                    self.write_output("-" * 50 + "\n")
                    
                    for i, (user_id, username, first_name, _, created_at) in enumerate(course_participants, 1):
                        self.write_output(f"{i}. {first_name or 'Без имени'} ")
                        self.write_output(f"(@{username or 'без username'})\n")
                        self.write_output(f"   ID: {user_id}, Дата: {created_at}\n\n")
                
                # Список ID для рассылки
                user_ids = [p[0] for p in participants]
                self.write_output(f"\n💬 User IDs для рассылки: {user_ids}\n", "info")
            
            self.status_var.set(f"Загружено {len(participants)} подтвержденных участников")
            
        except Exception as e:
            self.write_output(f"\nОшибка: {str(e)}\n", "error")
            self.status_var.set("Ошибка при загрузке данных")
    
    def show_unconfirmed(self):
        """Показать неподтвержденных участников"""
        self.clear_output()
        self.status_var.set("Загрузка неподтвержденных участников...")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, first_name, chosen_course, confirmed, created_at
                FROM bookings
                WHERE confirmed != 2
                ORDER BY confirmed, created_at DESC
            """)
            
            participants = cursor.fetchall()
            conn.close()
            
            self.write_output("⏳ НЕПОДТВЕРЖДЕННЫЕ УЧАСТНИКИ\n", "header")
            self.write_output("=" * 70 + "\n\n")
            
            if not participants:
                self.write_output("Все участники подтвердили оплату!\n", "success")
            else:
                # Группировка по статусам
                statuses = {
                    0: {"name": "🕐 Ожидают оплаты", "participants": []},
                    1: {"name": "📸 Загрузили чек (ожидают проверки)", "participants": []},
                    -1: {"name": "❌ Отменено", "participants": []}
                }
                
                for p in participants:
                    status = p[4]
                    if status in statuses:
                        statuses[status]["participants"].append(p)
                
                for status_code, status_info in statuses.items():
                    if status_info["participants"]:
                        self.write_output(f"\n{status_info['name']} ({len(status_info['participants'])} чел.)\n", "info")
                        self.write_output("-" * 50 + "\n")
                        
                        for i, (user_id, username, first_name, course, _, created_at) in enumerate(status_info["participants"], 1):
                            # Вычисляем время
                            created_dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                            time_passed = datetime.now() - created_dt
                            days = time_passed.days
                            hours = time_passed.seconds // 3600
                            
                            self.write_output(f"{i}. {first_name or 'Без имени'} ")
                            self.write_output(f"(@{username or 'без username'})\n")
                            self.write_output(f"   Курс: {course}\n")
                            self.write_output(f"   ID: {user_id}, Дата: {created_at}\n")
                            self.write_output(f"   Прошло: {days} дн. {hours} ч.\n")
                            
                            if status_code == 0 and days > 1:
                                self.write_output("   ⚠️  Не оплатил более суток!\n", "warning")
                            
                            self.write_output("\n")
            
            self.status_var.set(f"Загружено {len(participants)} неподтвержденных участников")
            
        except Exception as e:
            self.write_output(f"\nОшибка: {str(e)}\n", "error")
            self.status_var.set("Ошибка при загрузке данных")
    
    def prepare_messaging(self):
        """Подготовить рассылку сообщений"""
        self.clear_output()
        self.write_output("💬 ПОДГОТОВКА РАССЫЛКИ\n", "header")
        self.write_output("=" * 70 + "\n\n")
        
        try:
            # Запускаем скрипт рассылки
            result = subprocess.run([sys.executable, 'send_message_to_confirmed.py'], 
                                  capture_output=True, text=True)
            
            if result.stdout:
                self.write_output(result.stdout)
            if result.stderr:
                self.write_output(result.stderr, "error")
            
            self.write_output("\n⚠️  Рассылка находится в тестовом режиме!\n", "warning")
            self.write_output("Для реальной отправки раскомментируйте строки в send_message_to_confirmed.py\n")
            
        except Exception as e:
            self.write_output(f"\nОшибка: {str(e)}\n", "error")
    
    def delete_test_records(self):
        """Удалить тестовые записи"""
        # Сначала проверим, есть ли записи
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE username = 'r1iiis'")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            messagebox.showinfo("Информация", "Тестовые записи пользователя @r1iiis не найдены")
            return
        
        # Запрашиваем подтверждение
        result = messagebox.askyesno("Подтверждение", 
                                   f"Найдено {count} тестовых записей пользователя @r1iiis.\n\n"
                                   "Удалить их?")
        
        if result:
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bookings WHERE username = 'r1iiis'")
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Успех", f"Удалено {deleted} тестовых записей")
                self.refresh_data()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def refresh_data(self):
        """Обновить текущий вид"""
        self.show_statistics()
        self.status_var.set("Данные обновлены")

def main():
    root = tk.Tk()
    app = AdminPanel(root)
    root.mainloop()

if __name__ == "__main__":
    main()