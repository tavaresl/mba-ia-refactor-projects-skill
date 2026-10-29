import logging

from middlewares.errors import ApiError
from models import produto_model
from validators.payloads import validar_filtros_busca, validar_produto

logger = logging.getLogger(__name__)


def listar(conn):
    produtos = produto_model.listar(conn)
    logger.info("Listando %d produtos", len(produtos))
    return {"dados": produtos, "sucesso": True}, 200


def buscar_por_id(conn, produto_id):
    produto = produto_model.obter(conn, produto_id)
    if not produto:
        raise ApiError("Produto não encontrado", 404, sucesso=False)
    return {"dados": produto, "sucesso": True}, 200


def criar(conn, dados):
    campos = validar_produto(dados)
    produto_id = produto_model.criar(conn, **campos)
    logger.info("Produto criado com ID: %s", produto_id)
    return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar(conn, produto_id, dados):
    if not produto_model.obter(conn, produto_id):
        raise ApiError("Produto não encontrado", 404)
    campos = validar_produto(dados)
    produto_model.atualizar(conn, produto_id, **campos)
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar(conn, produto_id):
    if not produto_model.obter(conn, produto_id):
        raise ApiError("Produto não encontrado", 404)
    produto_model.deletar(conn, produto_id)
    logger.info("Produto %s deletado", produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200


def buscar(conn, args):
    resultados = produto_model.buscar(conn, **validar_filtros_busca(args))
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
