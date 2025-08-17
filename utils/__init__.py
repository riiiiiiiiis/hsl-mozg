# utils package

def escape_markdown_v2(text: str) -> str:
    """Helper function to escape text for MarkdownV2 parsing."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return "".join(f'\\{char}' if char in escape_chars else char for char in str(text))


def get_user_identification(user_data: dict) -> str:
    """
    Extract and format user identification with proper priority.
    
    Priority order:
    1. username (if available and not empty)
    2. first_name (if available and not empty) 
    3. user_id (as fallback)
    
    Args:
        user_data (dict): Dictionary containing user information with keys:
            - username (str, optional): Telegram username
            - first_name (str, optional): User's first name
            - user_id (int): Telegram user ID
            
    Returns:
        str: Formatted user identification string
        
    Examples:
        >>> get_user_identification({'username': 'john_doe', 'first_name': 'John', 'user_id': 123456})
        '@john_doe'
        >>> get_user_identification({'first_name': 'John', 'user_id': 123456})
        'John'
        >>> get_user_identification({'user_id': 123456})
        'ID: 123456'
    """
    if not user_data:
        return "Unknown User"
    
    # Priority 1: username (with @ prefix if available)
    username = user_data.get('username')
    if username and username.strip():
        return f"@{username.strip()}"
    
    # Priority 2: first_name
    first_name = user_data.get('first_name')
    if first_name and first_name.strip():
        return first_name.strip()
    
    # Priority 3: user_id as fallback
    user_id = user_data.get('user_id')
    if user_id is not None:
        return f"ID: {user_id}"
    
    return "Unknown User"


def get_course_flow_info(course_stream: str, start_date_text: str) -> str:
    """
    Format course flow number and start date information.
    
    Args:
        course_stream (str): Course stream identifier (e.g., '4th_stream', '3rd_stream')
        start_date_text (str): Human-readable start date (e.g., '1 сентября')
        
    Returns:
        str: Formatted course flow information
        
    Examples:
        >>> get_course_flow_info('4th_stream', '1 сентября')
        '4-й поток (старт 1 сентября)'
        >>> get_course_flow_info('3rd_stream', '15 августа')
        '3-й поток (старт 15 августа)'
        >>> get_course_flow_info('1st_stream', '1 октября')
        '1-й поток (старт 1 октября)'
    """
    if not course_stream or not start_date_text:
        return "Информация о потоке недоступна"
    
    # Extract stream number from course_stream
    stream_number = None
    if course_stream.endswith('_stream'):
        stream_part = course_stream.replace('_stream', '')
        try:
            # Handle ordinal numbers (1st, 2nd, 3rd, 4th, etc.)
            if stream_part.endswith('st'):
                stream_number = int(stream_part[:-2])
            elif stream_part.endswith('nd'):
                stream_number = int(stream_part[:-2])
            elif stream_part.endswith('rd'):
                stream_number = int(stream_part[:-2])
            elif stream_part.endswith('th'):
                stream_number = int(stream_part[:-2])
            else:
                # Try to parse as regular number
                stream_number = int(stream_part)
        except ValueError:
            # If parsing fails, use the original string
            pass
    
    if stream_number is not None:
        # Format with Russian ordinal suffix
        if stream_number == 1:
            ordinal_suffix = "первый"
        elif stream_number == 2:
            ordinal_suffix = "второй"
        elif stream_number == 3:
            ordinal_suffix = "третий"
        elif stream_number == 4:
            ordinal_suffix = "четвертый"
        elif stream_number == 5:
            ordinal_suffix = "пятый"
        else:
            ordinal_suffix = f"{stream_number}-й"
        
        return f"{ordinal_suffix} поток (старт {start_date_text})"
    else:
        # Fallback to original format if parsing fails
        return f"{course_stream} (старт {start_date_text})"


def get_approval_timestamp() -> str:
    """
    Generate UTC timestamp for approval status.
    
    Returns:
        str: Formatted UTC timestamp in format 'YYYY-MM-DD HH:MM UTC'
        
    Examples:
        >>> get_approval_timestamp()
        '2024-08-17 15:30 UTC'
    """
    from datetime import datetime, timezone
    utc_now = datetime.now(timezone.utc)
    return utc_now.strftime('%Y-%m-%d %H:%M UTC')