from flask import Blueprint, request

from controllers import produto_controller
from db.connection import get_db
from routes._http import corpo_json, responder

bp = Blueprint("produtos", __name__)


@bp.get("/produtos")
def listar_produtos():
    return responder(produto_controller.listar(get_db()))


@bp.get("/produtos/busca")
def buscar_produtos():
    return responder(produto_controller.buscar(get_db(), request.args))


@bp.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    return responder(produto_controller.buscar_por_id(get_db(), produto_id))


@bp.post("/produtos")
def criar_produto():
    return responder(produto_controller.criar(get_db(), corpo_json()))


@bp.put("/produtos/<int:produto_id>")
def atualizar_produto(produto_id):
    return responder(produto_controller.atualizar(get_db(), produto_id, corpo_json()))


@bp.delete("/produtos/<int:produto_id>")
def deletar_produto(produto_id):
    return responder(produto_controller.deletar(get_db(), produto_id))
