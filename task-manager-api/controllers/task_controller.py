import logging

from controllers.common import commit_or_fail
from middlewares.errors import ApiError
from models.category import Category
from models.database import db
from models.task import Task
from models.user import User
from validators import inputs as validators

logger = logging.getLogger(__name__)


def _user_exists(user_id):
    return User.find_by_id(user_id) is not None


def _category_exists(category_id):
    return Category.find_by_id(category_id) is not None


def find_task_or_404(task_id):
    task = Task.find_by_id(task_id)
    if not task:
        raise ApiError('Task não encontrada', 404)
    return task


def list_tasks():
    return [task.to_listing_dict() for task in Task.list_all_with_relations()]


def get_task(task_id):
    return find_task_or_404(task_id).to_detail_dict()


def create_task(data):
    fields = validators.validate_task_create(data, _user_exists, _category_exists)
    task = Task(**fields)
    db.session.add(task)
    commit_or_fail('Erro ao criar task')
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task.to_dict()


def update_task(task, data):
    fields = validators.validate_task_update(data, _user_exists, _category_exists)
    for name, value in fields.items():
        setattr(task, name, value)
    commit_or_fail('Erro ao atualizar')
    logger.info('Task atualizada: %s', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = find_task_or_404(task_id)
    db.session.delete(task)
    commit_or_fail('Erro ao deletar')
    logger.info('Task deletada: %s', task_id)


def search_tasks(args):
    filters = validators.parse_task_search_filters(args)
    return [task.to_dict() for task in Task.search(**filters)]
