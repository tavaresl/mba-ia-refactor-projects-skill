import logging
import sqlite3

from flask import current_app, jsonify

from config import constants
from middlewares.errors import ApiError, MENSAGEM_ERRO_INTERNO
from models import pedido_model, produto_model, usuario_model

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": constants.APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    try:
        counts = {
            "produtos": produto_model.contar(),
            "usuarios": usuario_model.contar(),
            "pedidos": pedido_model.contar(),
        }
    except sqlite3.Error:
        logger.exception("Falha no health check")
        raise ApiError({"status": "erro", "detalhes": MENSAGEM_ERRO_INTERNO}, 500)

    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": constants.APP_VERSION,
        "ambiente": current_app.config["APP_ENV"],
        "db_path": current_app.config["DB_PATH"],
        "debug": current_app.config["DEBUG"],
    }), 200
