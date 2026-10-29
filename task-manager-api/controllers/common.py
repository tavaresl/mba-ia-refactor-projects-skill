import logging

from sqlalchemy.exc import SQLAlchemyError

from middlewares.errors import ApiError
from models import db

logger = logging.getLogger(__name__)


def commit_or_fail(error_message):
    """Confirma a transação; em falha faz rollback e responde 500 com a mensagem da rota."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception('Falha ao gravar no banco: %s', error_message)
        raise ApiError(error_message, 500)
