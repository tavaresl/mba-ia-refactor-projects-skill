"""Conexão SQLite por requisição (flask.g) e utilitários de transação."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g

_ACOES_LEITURA = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    getattr(sqlite3, "SQLITE_RECURSIVE", 33),
}


def conectar(db_path):
    # isolation_level=None: autocommit; transações explícitas via transacao().
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def conectar_somente_leitura(db_path):
    """Conexão que só permite SELECT (modo ro + authorizer)."""
    conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.set_authorizer(
        lambda acao, *_: sqlite3.SQLITE_OK if acao in _ACOES_LEITURA else sqlite3.SQLITE_DENY
    )
    return conn


def get_db():
    if "db" not in g:
        g.db = conectar(current_app.config["DB_PATH"])
    return g.db


def fechar_db(_erro=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@contextmanager
def transacao(conn, imediata=False):
    """BEGIN/COMMIT com ROLLBACK em qualquer erro. imediata=True trava escritas desde o início."""
    conn.execute("BEGIN IMMEDIATE" if imediata else "BEGIN")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")
