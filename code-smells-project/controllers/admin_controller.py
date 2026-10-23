import logging
import sqlite3

from flask import jsonify

from middlewares.errors import ApiError
from models import admin_model
from validators import payloads

logger = logging.getLogger(__name__)


def reset_database():
    admin_model.resetar_banco()
    logger.warning("BANCO DE DADOS RESETADO")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    consulta = payloads.validar_query_admin(payloads.corpo_json())
    try:
        resultado = admin_model.consultar(consulta)
    except sqlite3.Error:
        logger.exception("Consulta administrativa recusada ou inválida")
        raise ApiError({"erro": "Consulta inválida ou não permitida"}, 400)
    return jsonify({"dados": resultado, "sucesso": True}), 200
