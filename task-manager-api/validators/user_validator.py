import re

from config.constants import EMAIL_PATTERN, MIN_PASSWORD_LENGTH, USER_ROLES
from middlewares.errors import ApiError
from validators.common import (
    require_bool,
    require_json_object,
    require_str,
)


def check_email_format(email):
    if not re.match(EMAIL_PATTERN, email):
        raise ApiError('Email inválido', 400)
    return email


def check_role(role):
    if role not in USER_ROLES:
        raise ApiError('Role inválido', 400)
    return role


def check_role_change(role, current_role, is_admin):
    """Papel diferente do atual/padrão só com a credencial de administrador."""
    if role != current_role and not is_admin:
        raise ApiError('Acesso negado', 403)


def validate_new_user(data):
    """Campos obrigatórios, tipos e formatos do POST /users."""
    require_json_object(data)

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name:
        raise ApiError('Nome é obrigatório', 400)
    if not email:
        raise ApiError('Email é obrigatório', 400)
    if not password:
        raise ApiError('Senha é obrigatória', 400)

    require_str(name)
    require_str(email)
    require_str(password)

    check_email_format(email)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ApiError('Senha deve ter no mínimo 4 caracteres', 400)

    return name, email, password


def check_name_on_update(name):
    require_str(name)
    if not name:
        raise ApiError('Nome é obrigatório', 400)
    return name


def check_password_on_update(password):
    require_str(password)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ApiError('Senha muito curta', 400)
    return password


def check_active(active):
    return require_bool(active)


def validate_login(data):
    require_json_object(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ApiError('Email e senha são obrigatórios', 400)
    require_str(email)
    require_str(password)
    return email, password
