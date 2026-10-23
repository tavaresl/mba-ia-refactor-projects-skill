import logging

from sqlalchemy.exc import SQLAlchemyError

from middlewares.errors import ApiError
from models.database import db
from models.user import User

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = 'Credenciais inválidas'


def authenticate(email, password):
    """Valida as credenciais e migra hashes MD5 antigos para o formato novo."""
    user = User.find_by_email(email)
    if not user:
        raise ApiError(INVALID_CREDENTIALS, 401)

    was_legacy = user.uses_legacy_hash()
    if not user.check_password(password):
        raise ApiError(INVALID_CREDENTIALS, 401)

    if was_legacy:
        _upgrade_password_hash(user, password)

    if not user.active:
        raise ApiError('Usuário inativo', 403)
    return user


def _upgrade_password_hash(user, password):
    try:
        user.set_password(password)
        db.session.commit()
        logger.info('Hash de senha migrado para o formato atual (user_id=%s)', user.id)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception('Falha ao migrar o hash de senha (user_id=%s)', user.id)
