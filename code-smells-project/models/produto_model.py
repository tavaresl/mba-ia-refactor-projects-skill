"""Acesso a dados de produtos (SQL parametrizado)."""
from db.connection import get_db

BUSCA_SQL = """
    SELECT * FROM produtos
    WHERE (:termo = '' OR nome LIKE '%' || :termo || '%' OR descricao LIKE '%' || :termo || '%')
      AND (:categoria IS NULL OR categoria = :categoria)
      AND (:preco_min IS NULL OR preco >= :preco_min)
      AND (:preco_max IS NULL OR preco <= :preco_max)
    ORDER BY id
"""


def para_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar():
    rows = get_db().execute("SELECT * FROM produtos ORDER BY id").fetchall()
    return [para_dict(row) for row in rows]


def buscar_row_por_id(produto_id):
    return get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()


def buscar_por_id(produto_id):
    row = buscar_row_por_id(produto_id)
    return para_dict(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    cursor = get_db().execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    get_db().execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )


def deletar(produto_id):
    get_db().execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def baixar_estoque(produto_id, quantidade):
    get_db().execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id)
    )


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    # Filtros 0/vazio são ignorados, como na API original.
    params = {
        "termo": termo or "",
        "categoria": categoria or None,
        "preco_min": preco_min or None,
        "preco_max": preco_max or None,
    }
    return [para_dict(row) for row in get_db().execute(BUSCA_SQL, params).fetchall()]


def contar():
    return get_db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
