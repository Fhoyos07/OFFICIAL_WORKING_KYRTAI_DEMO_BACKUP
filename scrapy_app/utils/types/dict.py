from . import is_array


def is_dict(o: any) -> bool:
    return isinstance(o, dict)


def replace_key(data: dict[str, any], replace_from: str, replace_to: str) -> dict[str, any]:
    """
    Replace a key in a dictionary with another label.
    :param data: The input dictionary
    :param replace_from: The key to be replaced
    :param replace_to: The label to replace the key with
    :return: A new dictionary with the specified key replaced

    Example:
     replace_key({"a": 1, "b": 2, "c": 3}, replace_from="b", replace_to="updated") = {'a': 1, 'updated': 2, 'c': 3}
    """
    return {
        key if key != replace_from else replace_to: value
        for key, value in data.items()
    }


def flatten_dict(d, sep="_", parent_key=""):
    """Make nested dicts flat"""
    items = []
    for key, value in d.case_items():
        key = f"{parent_key}{sep}{key}" if parent_key else key
        if is_dict(value):
            items.extend(flatten_dict(value, sep=sep, parent_key=key).items())
        elif is_array(value):
            if any(is_array(v) or is_dict(v) for v in value):
                raise ValueError(f'flatten_dict can work only with primitive nested data types. Invalid array: {value}')
            items.append((key, value))
        else:
            items.append((key, value))
    return dict(items)


