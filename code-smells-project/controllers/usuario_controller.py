import logging

from config.constants import TIPO_USUARIO_PADRAO
from middlewares.errors import ApiError
from models import usuario_model
from services import auth_service
from validators.payloads import validar_login, validar_usuario

logger = logging.getLogger(__name__)


def listar(conn):
    return {"dados": usuario_model.listar(conn), "sucesso": True}, 200


def buscar_por_id(conn, usuario_id):
    usuario = usuario_model.obter(conn, usuario_id)
    if not usuario:
        raise ApiError("Usuário não encontrado", 404)
    return {"dados": usuario, "sucesso": True}, 200


def criar(conn, dados):
    campos = validar_usuario(dados)
    # O tipo nunca vem do cliente: cadastro público é sempre o papel padrão (RF-16 nível 1).
    usuario_id = usuario_model.criar(
        conn, campos["nome"], campos["email"], auth_service.gerar_hash(campos["senha"]), TIPO_USUARIO_PADRAO
    )
    logger.info("Usuário criado: id %s", usuario_id)
    return {"dados": {"id": usuario_id}, "sucesso": True}, 201


def login(conn, dados):
    credenciais = validar_login(dados)
    for linha in usuario_model.buscar_por_email(conn, credenciais["email"]):
        confere, regravar = auth_service.verificar_senha(linha["senha"], credenciais["senha"])
        if confere:
            if regravar:
                usuario_model.atualizar_senha(conn, linha["id"], auth_service.gerar_hash(credenciais["senha"]))
            logger.info("Login bem-sucedido: usuário %s", linha["id"])
            return {"dados": usuario_model.serializar_login(linha), "sucesso": True, "mensagem": "Login OK"}, 200
    logger.info("Login falhou")
    raise ApiError("Email ou senha inválidos", 401, sucesso=False)
