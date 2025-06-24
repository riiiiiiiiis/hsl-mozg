def escape_markdown_v2(text: str) -> str:
    """Helper function to escape text for MarkdownV2 parsing."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return "".join(f'\\{char}' if char in escape_chars else char for char in str(text))