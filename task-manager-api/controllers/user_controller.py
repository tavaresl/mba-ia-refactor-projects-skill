import logging

from sqlalchemy import func, select

from config.constants import DEFAULT_ROLE, LOGIN_TOKEN_PREFIX
from controllers.common import commit_or_fail
from middlewares.errors import ApiError
from models import Task, User, db
from utils.dates import utc_now
from validators import user_validator as validator
from validators.common import require_json_object

logger = logging.getLogger(__name__)


def _get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)
    return user


def _tasks_of(user_id):
    return db.session.execute(
        select(Task).where(Task.user_id == user_id).order_by(Task.id)
    ).scalars().all()


def _email_taken(email, ignore_user_id=None):
    existing = db.session.execute(select(User).where(User.email == email)).scalars().first()
    return bool(existing) and existing.id != ignore_user_id


def list_users():
    users = db.session.execute(select(User).order_by(User.id)).scalars().all()
    task_counts = dict(db.session.execute(
        select(Task.user_id, func.count())
        .where(Task.user_id.isnot(None))
        .group_by(Task.user_id)
    ).all())

    result = []
    for user in users:
        data = user.to_dict()
        data['task_count'] = task_counts.get(user.id, 0)
        result.append(data)
    return result


def get_user(user_id):
    user = _get_user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in _tasks_of(user_id)]
    return data


def create_user(data, is_admin):
    name, email, password = validator.validate_new_user(data)
    if _email_taken(email):
        raise ApiError('Email já cadastrado', 409)

    role = validator.check_role(data.get('role', DEFAULT_ROLE))
    validator.check_role_change(role, DEFAULT_ROLE, is_admin)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    commit_or_fail('Erro ao criar usuário')
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict()


def update_user(user_id, read_body, is_admin):
    user = _get_user_or_404(user_id)
    data = read_body()
    require_json_object(data)

    changes = {}
    if 'name' in data:
        changes['name'] = validator.check_name_on_update(data['name'])
    if 'email' in data:
        email = validator.check_email_format(validator.require_str(data['email']))
        if _email_taken(email, ignore_user_id=user_id):
            raise ApiError('Email já cadastrado', 409)
        changes['email'] = email
    if 'password' in data:
        validator.check_password_on_update(data['password'])
    if 'role' in data:
        role = validator.check_role(data['role'])
        validator.check_role_change(role, user.role, is_admin)
        changes['role'] = role
    if 'active' in data:
        changes['active'] = validator.check_active(data['active'])

    for field, value in changes.items():
        setattr(user, field, value)
    if 'password' in data:
        user.set_password(data['password'])

    commit_or_fail('Erro ao atualizar')
    return user.to_dict()


def delete_user(user_id):
    user = _get_user_or_404(user_id)
    for task in _tasks_of(user_id):
        db.session.delete(task)
    db.session.delete(user)
    commit_or_fail('Erro ao deletar')
    logger.info('Usuário deletado: %s', user_id)
    return {'message': 'Usuário deletado com sucesso'}


def list_user_tasks(user_id):
    _get_user_or_404(user_id)
    now = utc_now()
    return [task.to_user_task_dict(now) for task in _tasks_of(user_id)]


def login(data):
    email, password = validator.validate_login(data)

    user = db.session.execute(select(User).where(User.email == email)).scalars().first()
    if not user:
        raise ApiError('Credenciais inválidas', 401)

    previous_hash = user.password
    if not user.check_password(password):
        raise ApiError('Credenciais inválidas', 401)
    if user.password != previous_hash:
        commit_or_fail('Erro interno')  # hash legado regravado no formato novo

    if not user.active:
        raise ApiError('Usuário inativo', 403)

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': LOGIN_TOKEN_PREFIX + str(user.id),
    }
