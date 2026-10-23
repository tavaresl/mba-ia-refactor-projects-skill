"""Acesso a dados de usuários (SQL parametrizado). Nunca serializa a senha."""
from config import constants
from db.connection import get_db


def para_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def resumo_login(row):
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios ORDER BY id").fetchall()
    return [para_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return para_dict(row) if row else None


def existe(usuario_id):
    return get_db().execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None


def buscar_rows_por_email(email):
    return get_db().execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()


def criar(nome, email, senha_hash, tipo=constants.TIPO_USUARIO_PADRAO):
    cursor = get_db().execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid


def atualizar_senha(usuario_id, senha_hash):
    get_db().execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))


def contar():
    return get_db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
