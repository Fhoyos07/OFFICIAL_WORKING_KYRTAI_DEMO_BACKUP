import re


def is_str(o: any) -> bool:
    """Check if param is string"""
    return isinstance(o, str)


def trim_spaces(s: str) -> str:
    """Remove unnecessary duplicated spaces"""
    return ' '.join(s.split()).strip()


def remove_all_spaces(s: str) -> str:
    """Remove all spaces"""
    return ' '.join(s.split()).strip()


def format_key(key: str) -> str:
    """Format title to key (without special characters, in lower case)"""
    key = re.sub(r'[^A-Za-z0-9\s]+', '', key)  # remove everything except letters, numbers and spaces
    key = trim_spaces(key).replace(' ', '_').lower()
    return key


def capitalize_first_letter(s: str) -> str:
    """Capitalize first letter of the string"""
    if s:
        return s[0].upper() + s[1:]
    return s
