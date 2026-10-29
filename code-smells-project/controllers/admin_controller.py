import logging

from models import admin_model
from validators.payloads import validar_consulta_admin

logger = logging.getLogger(__name__)


def resetar_banco(conn):
    admin_model.resetar(conn)
    logger.warning("BANCO DE DADOS RESETADO")
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200


def executar_query(db_path, dados):
    sql = validar_consulta_admin(dados)
    return {"dados": admin_model.consultar(db_path, sql), "sucesso": True}, 200
