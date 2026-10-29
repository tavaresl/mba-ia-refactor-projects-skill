import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from controllers.common import commit_or_fail
from middlewares.errors import ApiError
from models import Category, Task, User, db
from services import report_service
from utils.dates import utc_now
from validators import task_validator as validator
from validators.common import invalid_data, require_int_or_none, require_json_object, require_str_or_none

logger = logging.getLogger(__name__)


def _get_task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise ApiError('Task não encontrada', 404)
    return task


def _ensure_user_exists(user_id):
    if user_id is not None and not db.session.get(User, user_id):
        raise ApiError('Usuário não encontrado', 404)


def _ensure_category_exists(category_id):
    if category_id is not None and not db.session.get(Category, category_id):
        raise ApiError('Categoria não encontrada', 404)


def list_tasks():
    now = utc_now()
    tasks = db.session.execute(
        select(Task)
        .options(selectinload(Task.user), selectinload(Task.category))
        .order_by(Task.id)
    ).scalars().all()

    result = []
    for task in tasks:
        data = task.to_dict()
        data['overdue'] = task.is_overdue(now)
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result


def get_task(task_id):
    task = _get_task_or_404(task_id)
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def create_task(data):
    fields = validator.validate_new_task(data)
    _ensure_user_exists(fields['user_id'])
    _ensure_category_exists(fields['category_id'])
    fields.update(validator.optional_new_task_fields(data))

    task = Task(**fields)
    db.session.add(task)
    commit_or_fail('Erro ao criar task')
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task.to_dict()


def update_task(task_id, read_body):
    task = _get_task_or_404(task_id)
    data = read_body()
    require_json_object(data)

    changes = {}
    if 'title' in data:
        changes['title'] = validator.check_title(data['title'])
    if 'description' in data:
        changes['description'] = require_str_or_none(data['description'])
    if 'status' in data:
        changes['status'] = validator.check_status(data['status'])
    if 'priority' in data:
        changes['priority'] = validator.check_priority(data['priority'])
    if 'user_id' in data:
        user_id = require_int_or_none(data['user_id'])
        _ensure_user_exists(user_id)
        changes['user_id'] = user_id
    if 'category_id' in data:
        category_id = require_int_or_none(data['category_id'])
        _ensure_category_exists(category_id)
        changes['category_id'] = category_id
    if 'due_date' in data:
        due_date = data['due_date']
        changes['due_date'] = (
            validator.parse_due_date(due_date, validator.DATE_ERROR_ON_UPDATE)
            if due_date else None
        )
    if 'tags' in data:
        changes['tags'] = validator.tags_to_text(data['tags'])

    for field, value in changes.items():
        setattr(task, field, value)
    task.updated_at = utc_now()

    commit_or_fail('Erro ao atualizar')
    logger.info('Task atualizada: %s', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = _get_task_or_404(task_id)
    db.session.delete(task)
    commit_or_fail('Erro ao deletar')
    logger.info('Task deletada: %s', task_id)
    return {'message': 'Task deletada com sucesso'}


def _int_filter(raw_value):
    try:
        return int(raw_value)
    except ValueError:
        raise invalid_data()


def search_tasks(query_text, status, priority, user_id):
    statement = select(Task)

    if query_text:
        statement = statement.where(
            db.or_(
                Task.title.like(f'%{query_text}%'),
                Task.description.like(f'%{query_text}%'),
            )
        )
    if status:
        statement = statement.where(Task.status == status)
    if priority:
        statement = statement.where(Task.priority == _int_filter(priority))
    if user_id:
        statement = statement.where(Task.user_id == _int_filter(user_id))

    tasks = db.session.execute(statement.order_by(Task.id)).scalars().all()
    return [task.to_dict() for task in tasks]


def task_stats():
    return report_service.task_stats()
