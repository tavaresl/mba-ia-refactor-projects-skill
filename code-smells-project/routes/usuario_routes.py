from flask import Blueprint

from controllers import usuario_controller
from db.connection import get_db
from routes._http import corpo_json, responder

bp = Blueprint("usuarios", __name__)


@bp.get("/usuarios")
def listar_usuarios():
    return responder(usuario_controller.listar(get_db()))


@bp.get("/usuarios/<int:usuario_id>")
def buscar_usuario(usuario_id):
    return responder(usuario_controller.buscar_por_id(get_db(), usuario_id))


@bp.post("/usuarios")
def criar_usuario():
    return responder(usuario_controller.criar(get_db(), corpo_json()))


@bp.post("/login")
def login():
    return responder(usuario_controller.login(get_db(), corpo_json()))
