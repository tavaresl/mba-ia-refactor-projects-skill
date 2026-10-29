"""Exceção da aplicação e handler central de erros."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return error

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
