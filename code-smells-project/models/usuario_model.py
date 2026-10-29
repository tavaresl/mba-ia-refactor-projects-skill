"""Acesso a dados de usuários. A senha (hash) nunca sai nos serializers."""

COLUNAS_PUBLICAS = ("id", "nome", "email", "tipo", "criado_em")
COLUNAS_LOGIN = ("id", "nome", "email", "tipo")


def serializar(linha):
    return {coluna: linha[coluna] for coluna in COLUNAS_PUBLICAS}


def serializar_login(linha):
    return {coluna: linha[coluna] for coluna in COLUNAS_LOGIN}


def listar(conn):
    return [serializar(linha) for linha in conn.execute("SELECT * FROM usuarios").fetchall()]


def obter(conn, usuario_id):
    linha = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return serializar(linha) if linha else None


def existe(conn, usuario_id):
    return conn.execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None


def buscar_por_email(conn, email):
    """Linhas completas (com hash) para verificação de senha, na ordem de cadastro."""
    return conn.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()


def criar(conn, nome, email, senha_hash, tipo):
    cursor = conn.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid


def atualizar_senha(conn, usuario_id, senha_hash):
    conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
