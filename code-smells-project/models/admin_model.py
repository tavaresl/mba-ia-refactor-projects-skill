"""Operações administrativas: reset fixo e consulta somente-leitura."""
import logging
import sqlite3

from db.connection import conectar_somente_leitura, transacao
from middlewares.errors import ApiError

logger = logging.getLogger(__name__)

RESET_STATEMENTS = (
    "DELETE FROM itens_pedido",
    "DELETE FROM pedidos",
    "DELETE FROM produtos",
    "DELETE FROM usuarios",
)

MENSAGEM_CONSULTA_INVALIDA = "Consulta inválida ou não permitida"


def resetar(conn):
    with transacao(conn):
        for instrucao in RESET_STATEMENTS:
            conn.execute(instrucao)


def consultar(db_path, sql):
    """Executa uma consulta de leitura; qualquer outra coisa é recusada com 400."""
    conn = conectar_somente_leitura(db_path)
    try:
        cursor = conn.execute(sql)
        if cursor.description is None:
            raise ApiError(MENSAGEM_CONSULTA_INVALIDA, 400)
        return [dict(linha) for linha in cursor.fetchall()]
    except sqlite3.Error:
        logger.exception("Falha ao executar consulta administrativa")
        raise ApiError(MENSAGEM_CONSULTA_INVALIDA, 400)
    finally:
        conn.close()
