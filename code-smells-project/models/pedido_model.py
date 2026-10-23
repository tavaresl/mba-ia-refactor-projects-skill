"""Acesso a dados de pedidos e itens (SQL parametrizado, sem N+1)."""
from config import constants
from db.connection import get_db

PEDIDOS_TODOS_SQL = "SELECT * FROM pedidos ORDER BY id"
PEDIDOS_USUARIO_SQL = "SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id"

ITENS_TODOS_SQL = """
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM itens_pedido i
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    ORDER BY i.pedido_id, i.id
"""
ITENS_USUARIO_SQL = """
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM itens_pedido i
    JOIN pedidos p ON p.id = i.pedido_id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    WHERE p.usuario_id = ?
    ORDER BY i.pedido_id, i.id
"""

RELATORIO_SQL = """
    SELECT
        COUNT(*) AS total_pedidos,
        COALESCE(SUM(total), 0) AS faturamento,
        COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes,
        COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados,
        COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados
    FROM pedidos
"""


def _montar(pedidos_rows, itens_rows):
    pedidos = []
    por_id = {}
    for row in pedidos_rows:
        pedido = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        }
        por_id[row["id"]] = pedido
        pedidos.append(pedido)
    for item in itens_rows:
        pedido = por_id.get(item["pedido_id"])
        if pedido is not None:
            pedido["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] if item["produto_nome"] is not None else "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
    return pedidos


def listar_todos():
    db = get_db()
    return _montar(db.execute(PEDIDOS_TODOS_SQL).fetchall(), db.execute(ITENS_TODOS_SQL).fetchall())


def listar_por_usuario(usuario_id):
    db = get_db()
    return _montar(
        db.execute(PEDIDOS_USUARIO_SQL, (usuario_id,)).fetchall(),
        db.execute(ITENS_USUARIO_SQL, (usuario_id,)).fetchall(),
    )


def criar(usuario_id, total):
    cursor = get_db().execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, constants.STATUS_PENDENTE, total),
    )
    return cursor.lastrowid


def inserir_item(pedido_id, produto_id, quantidade, preco_unitario):
    get_db().execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def existe(pedido_id):
    return get_db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def atualizar_status(pedido_id, novo_status):
    get_db().execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))


def totais_para_relatorio():
    return get_db().execute(RELATORIO_SQL).fetchone()


def contar():
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
