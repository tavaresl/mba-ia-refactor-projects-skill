import logging

from controllers.common import commit_or_fail
from middlewares.errors import ApiError
from models.database import db
from models.task import Task
from models.user import User
from validators import inputs as validators
from services import auth_service

logger = logging.getLogger(__name__)


def _email_taken(email):
    return User.find_by_email(email) is not None


def _email_owner_id(email):
    existing = User.find_by_email(email)
    return existing.id if existing else None


def find_user_or_404(user_id):
    user = User.find_by_id(user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)
    return user


def list_users():
    result = []
    for user in User.list_all_with_tasks():
        data = user.to_dict()
        data['task_count'] = len(user.tasks)
        result.append(data)
    return result


def get_user(user_id):
    user = find_user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.list_for_user(user_id)]
    return data


def create_user(data):
    fields = validators.validate_user_create(data, _email_taken)
    user = User(name=fields['name'], email=fields['email'], role=fields['role'])
    user.set_password(fields['password'])
    db.session.add(user)
    commit_or_fail('Erro ao criar usuário')
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict()


def update_user(user, data):
    fields = validators.validate_user_update(data, user.id, _email_owner_id)
    password = fields.pop('password', None)
    for name, value in fields.items():
        setattr(user, name, value)
    if password is not None:
        user.set_password(password)
    commit_or_fail('Erro ao atualizar')
    return user.to_dict()


def delete_user(user_id):
    user = find_user_or_404(user_id)
    for task in Task.list_for_user(user_id):
        db.session.delete(task)
    db.session.delete(user)
    commit_or_fail('Erro ao deletar')
    logger.info('Usuário deletado: %s', user_id)


def list_user_tasks(user_id):
    find_user_or_404(user_id)
    return [task.to_summary_dict() for task in Task.list_for_user(user_id)]


def login(data):
    email, password = validators.validate_login(data)
    user = auth_service.authenticate(email, password)
    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id),
    }
