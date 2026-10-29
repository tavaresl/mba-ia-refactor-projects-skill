"""Regra de negócio de pedidos: validação de estoque, total e gravação atômica."""
from db.connection import transacao
from middlewares.errors import ApiError
from models import pedido_model, produto_model, usuario_model


def criar_pedido(conn, usuario_id, itens):
    with transacao(conn, imediata=True):
        if not usuario_model.existe(conn, usuario_id):
            raise ApiError("Usuário não encontrado", 400, sucesso=False)

        produtos = {}
        reservado = {}  # quantidade acumulada por produto (itens repetidos somam)
        total = 0
        for item in itens:
            produto_id, quantidade = item["produto_id"], item["quantidade"]
            if produto_id not in produtos:
                produtos[produto_id] = produto_model.obter(conn, produto_id)
            produto = produtos[produto_id]
            if produto is None:
                raise ApiError(f"Produto {produto_id} não encontrado", 400, sucesso=False)
            reservado[produto_id] = reservado.get(produto_id, 0) + quantidade
            if produto["estoque"] < reservado[produto_id]:
                raise ApiError(f"Estoque insuficiente para {produto['nome']}", 400, sucesso=False)
            total = total + (produto["preco"] * quantidade)

        pedido_id = pedido_model.criar(conn, usuario_id, total)
        for item in itens:
            produto = produtos[item["produto_id"]]
            pedido_model.inserir_item(conn, pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            produto_model.baixar_estoque(conn, item["produto_id"], item["quantidade"])

    return {"pedido_id": pedido_id, "total": total}
