import logging

from flask import jsonify, request

from middlewares.errors import ApiError
from models import produto_model
from validators import payloads

logger = logging.getLogger(__name__)


def _produto_ou_404(produto_id, com_sucesso_false=False):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        payload = {"erro": "Produto não encontrado"}
        if com_sucesso_false:
            payload["sucesso"] = False
        raise ApiError(payload, 404)
    return produto


def listar_produtos():
    produtos = produto_model.listar()
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(produto_id):
    produto = _produto_ou_404(produto_id, com_sucesso_false=True)
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto():
    campos = payloads.validar_produto(payloads.corpo_json())
    produto_id = produto_model.criar(*campos)
    logger.info("Produto criado com ID: %s", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(produto_id):
    dados = payloads.corpo_json()
    _produto_ou_404(produto_id)
    campos = payloads.validar_produto(dados)
    produto_model.atualizar(produto_id, *campos)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(produto_id):
    _produto_ou_404(produto_id)
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo, categoria, preco_min, preco_max = payloads.validar_filtros_busca(request.args)
    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
