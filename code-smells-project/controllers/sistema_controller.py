import logging
import sqlite3

from config.constants import VERSAO_API
from models import pedido_model, produto_model, usuario_model

logger = logging.getLogger(__name__)


def index():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSAO_API,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }, 200


def health(conn, ambiente):
    try:
        contagens = {
            "produtos": produto_model.contar(conn),
            "usuarios": usuario_model.contar(conn),
            "pedidos": pedido_model.contar(conn),
        }
    except sqlite3.Error:
        logger.exception("Health check falhou")
        return {"status": "erro", "detalhes": "Banco de dados indisponível"}, 500
    return {
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": VERSAO_API,
        "ambiente": ambiente,
    }, 200
