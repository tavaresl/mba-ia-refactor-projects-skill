from flask import jsonify

from models import pedido_model
from services import pedido_service
from validators import payloads


def criar_pedido():
    usuario_id, itens = payloads.validar_pedido(payloads.corpo_json())
    resultado = pedido_service.criar_pedido(usuario_id, itens)
    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_model.listar_por_usuario(usuario_id), "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": pedido_model.listar_todos(), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    novo_status = payloads.validar_status(payloads.corpo_json())
    pedido_service.atualizar_status(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
