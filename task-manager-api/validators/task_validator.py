from config.constants import (
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    TASK_STATUS_PENDING,
    TASK_STATUSES,
)
from middlewares.errors import ApiError
from utils.dates import parse_date
from validators.common import (
    invalid_data,
    require_int,
    require_int_or_none,
    require_json_object,
    require_str,
    require_str_or_none,
)

DATE_ERROR_ON_CREATE = 'Formato de data inválido. Use YYYY-MM-DD'
DATE_ERROR_ON_UPDATE = 'Formato de data inválido'


def check_title(title):
    require_str(title)
    if len(title) < MIN_TITLE_LENGTH:
        raise ApiError('Título muito curto', 400)
    if len(title) > MAX_TITLE_LENGTH:
        raise ApiError('Título muito longo', 400)
    return title


def check_status(status):
    if status not in TASK_STATUSES:
        raise ApiError('Status inválido', 400)
    return status


def check_priority(priority):
    require_int(priority)
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ApiError('Prioridade deve ser entre 1 e 5', 400)
    return priority


def parse_due_date(value, error_message):
    try:
        return parse_date(value)
    except (ValueError, TypeError):
        raise ApiError(error_message, 400)


def tags_to_text(tags):
    """Lista de textos vira 'a,b'; texto é mantido; outros tipos são inválidos."""
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise invalid_data()
        return ','.join(tags)
    return require_str_or_none(tags)


def validate_new_task(data):
    """Valida o corpo do POST /tasks (sem checar existência de user/category)."""
    require_json_object(data)

    title = data.get('title')
    if not title:
        raise ApiError('Título é obrigatório', 400)
    check_title(title)

    description = require_str_or_none(data.get('description', ''))
    status = check_status(data.get('status', TASK_STATUS_PENDING))
    priority = check_priority(data.get('priority', DEFAULT_PRIORITY))
    user_id = require_int_or_none(data.get('user_id'))
    category_id = require_int_or_none(data.get('category_id'))

    return {
        'title': title,
        'description': description,
        'status': status,
        'priority': priority,
        'user_id': user_id,
        'category_id': category_id,
    }


def optional_new_task_fields(data):
    """due_date e tags do POST: valores vazios são ignorados."""
    fields = {}
    if data.get('due_date'):
        fields['due_date'] = parse_due_date(data['due_date'], DATE_ERROR_ON_CREATE)
    if data.get('tags'):
        fields['tags'] = tags_to_text(data['tags'])
    return fields
