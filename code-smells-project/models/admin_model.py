"""Operações administrativas: reset com SQL fixo e consulta somente-leitura."""
from flask import current_app

from db.connection import open_readonly, transaction, get_db

RESET_STATEMENTS = (
    "DELETE FROM itens_pedido",
    "DELETE FROM pedidos",
    "DELETE FROM produtos",
    "DELETE FROM usuarios",
)


def resetar_banco():
    db = get_db()
    with transaction(db):
        for statement in RESET_STATEMENTS:
            db.execute(statement)


def consultar(sql):
    conn = open_readonly(current_app.config["DB_FILE"])
    try:
        return [dict(row) for row in conn.execute(sql).fetchall()]
    finally:
        conn.close()
