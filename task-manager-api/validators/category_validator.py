from config.constants import DEFAULT_COLOR
from middlewares.errors import ApiError
from validators.common import require_json_object, require_str, require_str_or_none


def validate_new_category(data):
    require_json_object(data)

    name = data.get('name')
    if not name:
        raise ApiError('Nome é obrigatório', 400)
    require_str(name)

    return {
        'name': name,
        'description': require_str_or_none(data.get('description', '')),
        'color': require_str_or_none(data.get('color', DEFAULT_COLOR)),
    }


def validate_category_update(data):
    """Corpo vazio é aceito (atualização sem mudanças); só campos presentes."""
    require_json_object(data, allow_empty=True)

    changes = {}
    if 'name' in data:
        name = require_str(data['name'])
        if not name:
            raise ApiError('Nome é obrigatório', 400)
        changes['name'] = name
    if 'description' in data:
        changes['description'] = require_str_or_none(data['description'])
    if 'color' in data:
        changes['color'] = require_str_or_none(data['color'])
    return changes
