"""Acesso a dados de pedidos e itens."""
from config.constants import (
    NOME_PRODUTO_DESCONHECIDO, STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE,
)


def criar(conn, usuario_id, total):
    cursor = conn.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, STATUS_PENDENTE, total),
    )
    return cursor.lastrowid


def inserir_item(conn, pedido_id, produto_id, quantidade, preco_unitario):
    conn.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(conn, pedido_id, novo_status):
    """Retorna quantos pedidos foram atualizados (0 = não existe)."""
    return conn.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
    ).rowcount


def listar(conn, usuario_id=None):
    """Pedidos com itens em uma única query (sem N+1), na ordem de inserção."""
    sql = """
        SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
               i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
               pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
    """
    parametros = []
    if usuario_id is not None:
        sql += " WHERE p.usuario_id = ?"
        parametros.append(usuario_id)
    sql += " ORDER BY p.id, i.id"

    pedidos = {}
    for linha in conn.execute(sql, parametros).fetchall():
        pedido = pedidos.setdefault(linha["pedido_id"], {
            "id": linha["pedido_id"],
            "usuario_id": linha["usuario_id"],
            "status": linha["status"],
            "total": linha["total"],
            "criado_em": linha["criado_em"],
            "itens": [],
        })
        if linha["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": linha["produto_id"],
                "produto_nome": linha["produto_nome"] or NOME_PRODUTO_DESCONHECIDO,
                "quantidade": linha["quantidade"],
                "preco_unitario": linha["preco_unitario"],
            })
    return list(pedidos.values())


def resumo_vendas(conn):
    linha = conn.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               SUM(total) AS faturamento,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()
    return dict(linha)


def contar(conn):
    return conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
