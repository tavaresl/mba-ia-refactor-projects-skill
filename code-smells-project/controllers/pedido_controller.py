from middlewares.errors import ApiError
from models import pedido_model
from services import notificacao_service, pedido_service
from validators.payloads import validar_pedido, validar_status_pedido


def criar(conn, dados):
    pedido = validar_pedido(dados)
    resultado = pedido_service.criar_pedido(conn, pedido["usuario_id"], pedido["itens"])
    notificacao_service.pedido_criado(resultado["pedido_id"], pedido["usuario_id"])
    return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201


def listar_por_usuario(conn, usuario_id):
    return {"dados": pedido_model.listar(conn, usuario_id), "sucesso": True}, 200


def listar_todos(conn):
    return {"dados": pedido_model.listar(conn), "sucesso": True}, 200


def atualizar_status(conn, pedido_id, dados):
    novo_status = validar_status_pedido(dados)
    if pedido_model.atualizar_status(conn, pedido_id, novo_status) == 0:
        raise ApiError("Pedido não encontrado", 404)
    notificacao_service.status_atualizado(pedido_id, novo_status)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200
