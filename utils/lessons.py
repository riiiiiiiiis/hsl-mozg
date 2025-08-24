"""
Утилиты для работы с бесплатными уроками
Загрузка из YAML и helper функции
"""
import os
import yaml
from datetime import datetime
from typing import Dict, Optional, Tuple

# Путь к файлу с данными уроков
LESSONS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'lessons.yaml')

# Кэш для хранения загруженных уроков
_lessons_cache = None

def load_lessons() -> Dict:
    """
    Загружает уроки из YAML файла
    
    Returns:
        Словарь с уроками
    """
    global _lessons_cache
    
    if _lessons_cache is not None:
        return _lessons_cache
    
    with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        lessons = data.get('lessons', {})
        
        # Преобразуем строковые datetime в объекты datetime
        for lesson_key, lesson_data in lessons.items():
            if 'datetime' in lesson_data and isinstance(lesson_data['datetime'], str):
                lesson_data['datetime'] = datetime.fromisoformat(lesson_data['datetime'])
        
        _lessons_cache = lessons
        return lessons

def get_all_lessons() -> Dict:
    """
    Получить все уроки
    
    Returns:
        Словарь всех уроков
    """
    return load_lessons()

def get_active_lessons() -> Dict:
    """
    Получить только активные уроки (is_active=True и время еще не прошло)
    
    Returns:
        Словарь активных уроков, которые еще не прошли
    """
    from datetime import datetime, timedelta, timezone
    lessons = load_lessons()
    
    # Получаем текущее время с учетом временной зоны
    current_time = datetime.now(timezone.utc)
    
    active_lessons = {}
    for k, v in lessons.items():
        # Проверяем что урок активен
        if not v.get('is_active', False):
            continue
        
        # Проверяем что время урока еще не прошло (с буфером в 2 часа после начала)
        lesson_datetime = v.get('datetime')
        if lesson_datetime:
            # Преобразуем lesson_datetime в UTC если у него есть временная зона
            if lesson_datetime.tzinfo is None:
                # Если нет временной зоны, считаем что это UTC
                lesson_datetime = lesson_datetime.replace(tzinfo=timezone.utc)
            else:
                # Конвертируем в UTC для сравнения
                lesson_datetime = lesson_datetime.astimezone(timezone.utc)
            
            # Даем 2 часа после начала урока перед тем как скрыть его
            grace_period = timedelta(hours=2)
            if current_time <= lesson_datetime + grace_period:
                active_lessons[k] = v
        else:
            # Если нет datetime, показываем урок (для обратной совместимости)
            active_lessons[k] = v
    
    return active_lessons

def get_lesson_by_id(lesson_id: int) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Найти урок по ID
    
    Args:
        lesson_id: ID урока
    
    Returns:
        Кортеж (lesson_type, lesson_data) или (None, None) если не найден
    """
    lessons = load_lessons()
    for lesson_type, lesson_data in lessons.items():
        if lesson_data.get('id') == lesson_id:
            return lesson_type, lesson_data
    return None, None

def get_lesson_by_type(lesson_type: str) -> Optional[Dict]:
    """
    Получить данные урока по типу
    
    Args:
        lesson_type: Тип урока (ключ в словаре)
    
    Returns:
        Данные урока или None
    """
    lessons = load_lessons()
    return lessons.get(lesson_type)

def get_all_lesson_types() -> list:
    """
    Получить все доступные типы уроков
    
    Returns:
        Список всех lesson_type (ключей) из YAML файла
    """
    lessons = load_lessons()
    return list(lessons.keys())

def reload_lessons():
    """
    Перезагрузить уроки из файла (сбросить кэш)
    """
    global _lessons_cache
    _lessons_cache = None