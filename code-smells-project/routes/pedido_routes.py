from flask import Blueprint

from controllers import pedido_controller
from db.connection import get_db
from routes._http import corpo_json, responder

bp = Blueprint("pedidos", __name__)


@bp.post("/pedidos")
def criar_pedido():
    return responder(pedido_controller.criar(get_db(), corpo_json()))


@bp.get("/pedidos")
def listar_todos_pedidos():
    return responder(pedido_controller.listar_todos(get_db()))


@bp.get("/pedidos/usuario/<int:usuario_id>")
def listar_pedidos_usuario(usuario_id):
    return responder(pedido_controller.listar_por_usuario(get_db(), usuario_id))


@bp.put("/pedidos/<int:pedido_id>/status")
def atualizar_status_pedido(pedido_id):
    return responder(pedido_controller.atualizar_status(get_db(), pedido_id, corpo_json()))
