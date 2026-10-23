import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = 'Erro interno'


class ApiError(Exception):
    """Erro esperado da API: vira {'error': mensagem} com o status informado."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({'error': error.message}), error.status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error
        logger.exception('Erro não tratado')
        return jsonify({'error': INTERNAL_ERROR_MESSAGE}), 500
