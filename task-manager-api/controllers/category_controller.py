from sqlalchemy import func, select

from controllers.common import commit_or_fail
from middlewares.errors import ApiError
from models import Category, Task, db
from validators import category_validator as validator


def _get_category_or_404(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise ApiError('Categoria não encontrada', 404)
    return category


def list_categories():
    categories = db.session.execute(select(Category).order_by(Category.id)).scalars().all()
    task_counts = dict(db.session.execute(
        select(Task.category_id, func.count())
        .where(Task.category_id.isnot(None))
        .group_by(Task.category_id)
    ).all())

    result = []
    for category in categories:
        data = category.to_dict()
        data['task_count'] = task_counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    category = Category(**validator.validate_new_category(data))
    db.session.add(category)
    commit_or_fail('Erro ao criar categoria')
    return category.to_dict()


def update_category(category_id, read_body):
    category = _get_category_or_404(category_id)
    for field, value in validator.validate_category_update(read_body()).items():
        setattr(category, field, value)
    commit_or_fail('Erro ao atualizar')
    return category.to_dict()


def delete_category(category_id):
    category = _get_category_or_404(category_id)
    db.session.delete(category)
    commit_or_fail('Erro ao deletar')
    return {'message': 'Categoria deletada'}
