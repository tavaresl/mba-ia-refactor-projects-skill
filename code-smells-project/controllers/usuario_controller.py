import logging

from flask import jsonify

from middlewares.errors import ApiError
from models import usuario_model
from services import auth_service
from validators import payloads

logger = logging.getLogger(__name__)


def listar_usuarios():
    return jsonify({"dados": usuario_model.listar(), "sucesso": True}), 200


def buscar_usuario(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        raise ApiError({"erro": "Usuário não encontrado"}, 404)
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    nome, email, senha = payloads.validar_novo_usuario(payloads.corpo_json())
    usuario_id = usuario_model.criar(nome, email, auth_service.hash_senha(senha))
    logger.info("Usuário criado: id=%s", usuario_id)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    email, senha = payloads.validar_login(payloads.corpo_json())
    usuario = auth_service.autenticar(email, senha)
    if not usuario:
        logger.info("Login falhou")
        raise ApiError({"erro": "Email ou senha inválidos", "sucesso": False}, 401)
    logger.info("Login bem-sucedido: usuario_id=%s", usuario["id"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
