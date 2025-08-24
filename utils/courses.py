"""
Утилиты для работы с курсами
Загрузка из YAML и helper функции
"""
import os
import yaml
from typing import List, Optional, Dict
from utils.course_validation import validate_course_id

# Путь к файлу с данными курсов
COURSES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'courses.yaml')

# Кэш для хранения загруженных курсов
_courses_cache = None

def load_courses() -> List[Dict]:
    """
    Загружает курсы из YAML файла
    
    Returns:
        Список курсов
    """
    global _courses_cache
    
    if _courses_cache is not None:
        return _courses_cache
    
    with open(COURSES_FILE, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        courses = data.get('courses', [])
        
        # Автоматически вычисляем price_usd_cents если не указано
        for course in courses:
            if 'price_usd_cents' not in course:
                course['price_usd_cents'] = int(course['price_usd'] * 100)
        
        _courses_cache = courses
        return courses

def get_all_courses() -> List[Dict]:
    """
    Получить все курсы
    
    Returns:
        Список всех курсов
    """
    return load_courses()

def get_active_courses() -> List[Dict]:
    """
    Получить только активные курсы
    
    Returns:
        Список активных курсов
    """
    courses = load_courses()
    return [c for c in courses if c.get('is_active', True)]

def get_course_by_id(course_id) -> Optional[Dict]:
    """
    Получить курс по ID с валидацией
    
    Args:
        course_id: ID курса (int или str)
    
    Returns:
        Данные курса или None
    """
    # Validate course ID
    validated_id = validate_course_id(course_id)
    if validated_id is None:
        return None
    
    courses = load_courses()
    for course in courses:
        if course.get('id') == validated_id:
            return course
    return None

def reload_courses():
    """
    Перезагрузить курсы из файла (сбросить кэш)
    """
    global _courses_cache
    _courses_cache = None