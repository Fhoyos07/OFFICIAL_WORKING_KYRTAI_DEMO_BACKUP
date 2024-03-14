from datetime import datetime


TOP_TIMEZONES = [
    "America/Chicago",
    "America/Los_Angeles",
    "America/Mexico_City",
    "America/New_York",
    "America/Sao_Paulo",
    "America/Toronto",
    "Europe/Amsterdam",
    "Europe/Berlin",
    "Europe/Istanbul",
    "Europe/Kyiv",
    "Europe/London",
    "Europe/Madrid",
    "Europe/Oslo",
    "Europe/Paris",
    "Europe/Rome",
    "Europe/Stockholm",
    "Europe/Warsaw",
    "Europe/Zurich",
    "Asia/Bangkok",
    "Asia/Dhaka",
    "Asia/Dubai",
    "Asia/Ho_Chi_Minh",
    "Asia/Hong_Kong",
    "Asia/Jakarta",
    "Asia/Karachi",
    "Asia/Kolkata",
    "Asia/Kuala_Lumpur",
    "Asia/Riyadh",
    "Asia/Seoul",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Asia/Taipei",
    "Asia/Tel_Aviv",
    "Asia/Tokyo",
    "Australia/Sydney",
    "Africa/Johannesburg",
]


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
