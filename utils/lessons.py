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
    Получить только активные уроки
    
    Returns:
        Словарь активных уроков
    """
    lessons = load_lessons()
    return {k: v for k, v in lessons.items() if v.get('is_active', False)}

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

def reload_lessons():
    """
    Перезагрузить уроки из файла (сбросить кэш)
    """
    global _lessons_cache
    _lessons_cache = None