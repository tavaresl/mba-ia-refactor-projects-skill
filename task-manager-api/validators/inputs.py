"""Validação de entrada. Mantém a ordem e as mensagens originais de cada rota."""
from datetime import datetime

from middlewares.errors import ApiError
from models.category import DEFAULT_COLOR
from models.task import (DEFAULT_PRIORITY, DEFAULT_STATUS, PRIORITY_MAX,
                         PRIORITY_MIN, TASK_STATUSES, TITLE_MAX_LENGTH,
                         TITLE_MIN_LENGTH)
from models.user import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, USER_ROLES, User

INVALID_DATA = 'Dados inválidos'
DATE_FORMAT = '%Y-%m-%d'


def invalid_data():
    return ApiError(INVALID_DATA, 400)


def require_object(data):
    """Corpo obrigatório: JSON vazio ou que não seja objeto é 'Dados inválidos'."""
    if not data or not isinstance(data, dict):
        raise invalid_data()
    return data


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_text_or_none(value):
    return value is None or isinstance(value, str)


def _check_reference_type(value):
    if not (value is None or _is_int(value) or isinstance(value, str)):
        raise invalid_data()


def _check_title_length(title):
    if len(title) < TITLE_MIN_LENGTH:
        raise ApiError('Título muito curto', 400)
    if len(title) > TITLE_MAX_LENGTH:
        raise ApiError('Título muito longo', 400)


def _check_status(status):
    if status not in TASK_STATUSES:
        raise ApiError('Status inválido', 400)


def _check_priority(priority):
    if not _is_int(priority):
        raise invalid_data()
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ApiError('Prioridade deve ser entre 1 e 5', 400)


def _parse_due_date(value, message):
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (ValueError, TypeError):
        raise ApiError(message, 400)


def _join_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise invalid_data()
        return ','.join(tags)
    if not _is_text_or_none(tags):
        raise invalid_data()
    return tags


def validate_task_create(data, user_exists, category_exists):
    data = require_object(data)

    title = data.get('title')
    if not title:
        raise ApiError('Título é obrigatório', 400)
    if not isinstance(title, str):
        raise invalid_data()
    _check_title_length(title)

    description = data.get('description', '')
    if not _is_text_or_none(description):
        raise invalid_data()
    status = data.get('status', DEFAULT_STATUS)
    priority = data.get('priority', DEFAULT_PRIORITY)
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    due_date = data.get('due_date')
    tags = data.get('tags')

    _check_status(status)
    _check_priority(priority)

    _check_reference_type(user_id)
    if user_id and not user_exists(user_id):
        raise ApiError('Usuário não encontrado', 404)
    _check_reference_type(category_id)
    if category_id and not category_exists(category_id):
        raise ApiError('Categoria não encontrada', 404)

    fields = {
        'title': title,
        'description': description,
        'status': status,
        'priority': priority,
        'user_id': user_id,
        'category_id': category_id,
    }
    if due_date:
        fields['due_date'] = _parse_due_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
    if tags:
        fields['tags'] = _join_tags(tags)
    return fields


def validate_task_update(data, user_exists, category_exists):
    data = require_object(data)
    fields = {}

    if 'title' in data:
        title = data['title']
        if not isinstance(title, str):
            raise invalid_data()
        _check_title_length(title)
        fields['title'] = title

    if 'description' in data:
        if not _is_text_or_none(data['description']):
            raise invalid_data()
        fields['description'] = data['description']

    if 'status' in data:
        _check_status(data['status'])
        fields['status'] = data['status']

    if 'priority' in data:
        _check_priority(data['priority'])
        fields['priority'] = data['priority']

    if 'user_id' in data:
        _check_reference_type(data['user_id'])
        if data['user_id'] and not user_exists(data['user_id']):
            raise ApiError('Usuário não encontrado', 404)
        fields['user_id'] = data['user_id']

    if 'category_id' in data:
        _check_reference_type(data['category_id'])
        if data['category_id'] and not category_exists(data['category_id']):
            raise ApiError('Categoria não encontrada', 404)
        fields['category_id'] = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            fields['due_date'] = _parse_due_date(data['due_date'], 'Formato de data inválido')
        else:
            fields['due_date'] = None

    if 'tags' in data:
        fields['tags'] = _join_tags(data['tags'])

    return fields


def parse_task_search_filters(args):
    try:
        priority = int(args.get('priority')) if args.get('priority') else None
        user_id = int(args.get('user_id')) if args.get('user_id') else None
    except ValueError:
        raise invalid_data()
    return {
        'text': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': priority,
        'user_id': user_id,
    }


def validate_user_create(data, email_taken):
    data = require_object(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ApiError('Nome é obrigatório', 400)
    if not email:
        raise ApiError('Email é obrigatório', 400)
    if not password:
        raise ApiError('Senha é obrigatória', 400)
    if not all(isinstance(value, str) for value in (name, email, password)):
        raise invalid_data()

    if not User.is_valid_email(email):
        raise ApiError('Email inválido', 400)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ApiError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres', 400)
    if email_taken(email):
        raise ApiError('Email já cadastrado', 409)
    if role not in USER_ROLES:
        raise ApiError('Role inválido', 400)

    return {'name': name, 'email': email, 'password': password, 'role': role}


def validate_user_update(data, user_id, email_owner_id):
    data = require_object(data)
    fields = {}

    if 'name' in data:
        if not data['name']:
            raise ApiError('Nome é obrigatório', 400)
        if not isinstance(data['name'], str):
            raise invalid_data()
        fields['name'] = data['name']

    if 'email' in data:
        email = data['email']
        if not isinstance(email, str):
            raise invalid_data()
        if not User.is_valid_email(email):
            raise ApiError('Email inválido', 400)
        owner_id = email_owner_id(email)
        if owner_id is not None and owner_id != user_id:
            raise ApiError('Email já cadastrado', 409)
        fields['email'] = email

    if 'password' in data:
        if not isinstance(data['password'], str):
            raise invalid_data()
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ApiError('Senha muito curta', 400)
        fields['password'] = data['password']

    if 'role' in data:
        if data['role'] not in USER_ROLES:
            raise ApiError('Role inválido', 400)
        fields['role'] = data['role']

    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise invalid_data()
        fields['active'] = data['active']

    return fields


def validate_login(data):
    data = require_object(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ApiError('Email e senha são obrigatórios', 400)
    if not isinstance(email, str) or not isinstance(password, str):
        raise invalid_data()
    return email, password


def validate_category_create(data):
    data = require_object(data)
    name = data.get('name')
    if not name:
        raise ApiError('Nome é obrigatório', 400)
    description = data.get('description', '')
    color = data.get('color', DEFAULT_COLOR)
    if not isinstance(name, str) or not _is_text_or_none(description) or not _is_text_or_none(color):
        raise invalid_data()
    return {'name': name, 'description': description, 'color': color}


def validate_category_update(data):
    if not isinstance(data, dict):
        raise invalid_data()
    fields = {}
    if 'name' in data:
        if not data['name']:
            raise ApiError('Nome é obrigatório', 400)
        if not isinstance(data['name'], str):
            raise invalid_data()
        fields['name'] = data['name']
    for key in ('description', 'color'):
        if key in data:
            if not _is_text_or_none(data[key]):
                raise invalid_data()
            fields[key] = data[key]
    return fields
