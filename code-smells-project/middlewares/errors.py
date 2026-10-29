"""Exceção da aplicação e tratamento central de erros."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


class ApiError(Exception):
    """Erro previsto: vira resposta {"erro": mensagem, **extra} com o status dado."""

    def __init__(self, mensagem, status=400, **extra):
        super().__init__(mensagem)
        self.status = status
        self.payload = {"erro": mensagem, **extra}


def registrar_handlers(app):
    @app.errorhandler(ApiError)
    def tratar_api_error(erro):
        return jsonify(erro.payload), erro.status

    @app.errorhandler(HTTPException)
    def tratar_http(erro):
        return erro  # 404/405 etc. mantêm a resposta padrão do Flask

    @app.errorhandler(Exception)
    def tratar_inesperado(erro):
        logger.exception("Erro inesperado")
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500
