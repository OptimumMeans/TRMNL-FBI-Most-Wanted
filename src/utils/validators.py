import re

def sanitize_string(input_str: str, max_length: int = 100) -> str:
    if not isinstance(input_str, str):
        return ''
    
    # Remove any non-printable characters
    clean_str = ''.join(char for char in input_str if char.isprintable())
    
    # Remove any potential HTML/script tags
    clean_str = re.sub(r'<[^>]*>', '', clean_str)
    
    return clean_str[:max_length]