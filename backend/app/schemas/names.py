def strip_name(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value