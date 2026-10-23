from controllers.common import commit_or_fail
from middlewares.errors import ApiError
from models.category import Category
from models.database import db
from models.task import Task
from validators import inputs as validators


def find_category_or_404(category_id):
    category = Category.find_by_id(category_id)
    if not category:
        raise ApiError('Categoria não encontrada', 404)
    return category


def list_categories():
    task_counts = Task.count_grouped(Task.category_id)
    result = []
    for category in Category.list_all():
        data = category.to_dict()
        data['task_count'] = task_counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    fields = validators.validate_category_create(data)
    category = Category(**fields)
    db.session.add(category)
    commit_or_fail('Erro ao criar categoria')
    return category.to_dict()


def update_category(category, data):
    fields = validators.validate_category_update(data)
    for name, value in fields.items():
        setattr(category, name, value)
    commit_or_fail('Erro ao atualizar')
    return category.to_dict()


def delete_category(category_id):
    category = find_category_or_404(category_id)
    db.session.delete(category)
    commit_or_fail('Erro ao deletar')
