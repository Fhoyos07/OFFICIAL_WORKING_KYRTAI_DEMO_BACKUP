from datetime import datetime


def format_date_string_to_iso(date_string: str, source_format: str) -> str:
    """Parse and convert date string to ISO pretty format (2023-12-17)"""
    try:
        dt = datetime.strptime(date_string.strip(), source_format)
        return dt.date().isoformat()
    except ValueError:
        return date_string


def format_datetime_to_iso(dt: datetime) -> str:
    """Convert datetime object to ISO pretty format (2023-12-17 13:00:34)"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")  # .isoformat().replace('T', ' ').split('.')[0]
