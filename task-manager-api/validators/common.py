"""Checagens de tipo/forma reutilizadas pelos validators."""
from middlewares.errors import ApiError

INVALID_DATA = 'Dados inválidos'


def invalid_data():
    return ApiError(INVALID_DATA, 400)


def require_json_object(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise invalid_data()


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_str(value):
    if not isinstance(value, str):
        raise invalid_data()
    return value


def require_str_or_none(value):
    if value is not None and not isinstance(value, str):
        raise invalid_data()
    return value


def require_int(value):
    if not is_int(value):
        raise invalid_data()
    return value


def require_int_or_none(value):
    if value is not None and not is_int(value):
        raise invalid_data()
    return value


def require_bool(value):
    if not isinstance(value, bool):
        raise invalid_data()
    return value
