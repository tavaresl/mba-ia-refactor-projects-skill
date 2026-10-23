"""Regras de negócio de pedidos."""
from collections import defaultdict

from db.connection import get_db, transaction
from middlewares.errors import ApiError
from models import pedido_model, produto_model, usuario_model
from services import notificacao_service


def _erro_pedido(mensagem):
    return ApiError({"erro": mensagem, "sucesso": False}, 400)


def criar_pedido(usuario_id, itens):
    """Cria pedido, itens e baixa de estoque numa única transação."""
    with transaction(get_db()):
        if not usuario_model.existe(usuario_id):
            raise _erro_pedido("Usuário não encontrado")

        total = 0
        acumulado = defaultdict(int)
        linhas = []
        for item in itens:
            produto_id, quantidade = item["produto_id"], item["quantidade"]
            produto = produto_model.buscar_row_por_id(produto_id)
            if produto is None:
                raise _erro_pedido("Produto " + str(produto_id) + " não encontrado")
            # soma por produto: itens repetidos não podem furar o limite de estoque
            acumulado[produto_id] += quantidade
            if produto["estoque"] < acumulado[produto_id]:
                raise _erro_pedido("Estoque insuficiente para " + produto["nome"])
            total = total + (produto["preco"] * quantidade)
            linhas.append((produto_id, quantidade, produto["preco"]))

        pedido_id = pedido_model.criar(usuario_id, total)
        for produto_id, quantidade, preco in linhas:
            pedido_model.inserir_item(pedido_id, produto_id, quantidade, preco)
            produto_model.baixar_estoque(produto_id, quantidade)

    notificacao_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, novo_status):
    if not pedido_model.existe(pedido_id):
        raise ApiError({"erro": "Pedido não encontrado"}, 404)
    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.status_alterado(pedido_id, novo_status)
