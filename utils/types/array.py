def is_array(o: any) -> bool:
    return any(isinstance(o, t) for t in (list, set, tuple))
