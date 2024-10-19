def to_bool(s: str | int | bool | None) -> bool | None:
    if s is None:
        return None
    if isinstance(s, str):
        s = s.lower()

    if s in (True, 'true', 'yes', 1):
        return True
    elif s in (False, 'false', 'no', 0):
        return False
    else:
        raise ValueError(f"Invalid value: {s}")
