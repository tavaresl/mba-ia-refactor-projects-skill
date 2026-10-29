"""Acesso a dados de produtos (SQL parametrizado, sem HTTP)."""

COLUNAS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def serializar(linha):
    return {coluna: linha[coluna] for coluna in COLUNAS}


def listar(conn):
    return [serializar(linha) for linha in conn.execute("SELECT * FROM produtos").fetchall()]


def obter(conn, produto_id):
    linha = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return serializar(linha) if linha else None


def criar(conn, nome, descricao, preco, estoque, categoria):
    cursor = conn.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def atualizar(conn, produto_id, nome, descricao, preco, estoque, categoria):
    conn.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )


def deletar(conn, produto_id):
    conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def baixar_estoque(conn, produto_id, quantidade):
    conn.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id))


def buscar(conn, termo, categoria=None, preco_min=None, preco_max=None):
    # Só trechos SQL fixos são concatenados; todos os valores vão como parâmetros.
    sql = "SELECT * FROM produtos WHERE 1=1"
    parametros = []
    if termo:
        sql += " AND (nome LIKE ? OR descricao LIKE ?)"
        parametros += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        sql += " AND categoria = ?"
        parametros.append(categoria)
    if preco_min:
        sql += " AND preco >= ?"
        parametros.append(preco_min)
    if preco_max:
        sql += " AND preco <= ?"
        parametros.append(preco_max)
    return [serializar(linha) for linha in conn.execute(sql, parametros).fetchall()]


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
