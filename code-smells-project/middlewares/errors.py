"""Exceção da aplicação e handler central de erros."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


class ApiError(Exception):
    """Erro de negócio/validação. `payload` é o corpo JSON exato da resposta."""

    def __init__(self, payload, status=400):
        super().__init__(str(payload))
        self.payload = payload
        self.status = status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify(error.payload), error.status

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):
            return error
        logger.exception("Erro não tratado")
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500
