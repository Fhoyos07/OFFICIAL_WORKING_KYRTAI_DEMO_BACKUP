import re


def parse_float(s: str | None) -> float:
    s = re.sub('[^0-9.]', '', s)
    return float(s) if s else None
