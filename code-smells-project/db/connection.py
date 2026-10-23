"""Conexão SQLite por requisição (flask.g) e utilitários de transação."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g

_ALLOWED_READ_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    getattr(sqlite3, "SQLITE_RECURSIVE", -1),
}


def get_db():
    if "db" not in g:
        # autocommit: transações multi-etapa são explícitas via transaction()
        g.db = sqlite3.connect(current_app.config["DB_FILE"], isolation_level=None)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transaction(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    else:
        db.execute("COMMIT")


def _only_reads(action, *_args):
    return sqlite3.SQLITE_OK if action in _ALLOWED_READ_ACTIONS else sqlite3.SQLITE_DENY


def open_readonly(db_file):
    """Conexão somente-leitura (modo ro + authorizer) para consultas administrativas."""
    uri = Path(db_file).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.set_authorizer(_only_reads)
    return conn
