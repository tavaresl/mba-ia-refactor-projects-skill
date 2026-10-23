"""Validação de forma e tipo dos payloads. Mensagens idênticas às da API original."""
from flask import request

from config import constants
from middlewares.errors import ApiError

MSG_DADOS_INVALIDOS = "Dados inválidos"


def corpo_json():
    """Corpo JSON ou None (ausente, malformado ou sem Content-Type JSON)."""
    return request.get_json(silent=True)


def _eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _exigir_dict(dados, mensagem=MSG_DADOS_INVALIDOS):
    if not dados or not isinstance(dados, dict):
        raise ApiError({"erro": mensagem}, 400)
    return dados


def validar_produto(dados):
    dados = _exigir_dict(dados)
    if "nome" not in dados:
        raise ApiError({"erro": "Nome é obrigatório"}, 400)
    if "preco" not in dados:
        raise ApiError({"erro": "Preço é obrigatório"}, 400)
    if "estoque" not in dados:
        raise ApiError({"erro": "Estoque é obrigatório"}, 400)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", constants.CATEGORIA_PADRAO)

    textos_validos = all(isinstance(v, str) for v in (nome, descricao, categoria))
    if not textos_validos or not _eh_numero(preco) or not _eh_inteiro(estoque):
        raise ApiError({"erro": MSG_DADOS_INVALIDOS}, 400)

    if preco < 0:
        raise ApiError({"erro": "Preço não pode ser negativo"}, 400)
    if estoque < 0:
        raise ApiError({"erro": "Estoque não pode ser negativo"}, 400)
    if len(nome) < constants.NOME_PRODUTO_MIN:
        raise ApiError({"erro": "Nome muito curto"}, 400)
    if len(nome) > constants.NOME_PRODUTO_MAX:
        raise ApiError({"erro": "Nome muito longo"}, 400)
    if categoria not in constants.CATEGORIAS_VALIDAS:
        raise ApiError({"erro": "Categoria inválida. Válidas: " + str(constants.CATEGORIAS_VALIDAS)}, 400)

    return nome, descricao, preco, estoque, categoria


def validar_filtros_busca(args):
    termo = args.get("q", "")
    categoria = args.get("categoria") or None
    try:
        preco_min = float(args["preco_min"]) if args.get("preco_min") else None
        preco_max = float(args["preco_max"]) if args.get("preco_max") else None
    except ValueError:
        raise ApiError({"erro": MSG_DADOS_INVALIDOS}, 400)
    return termo, categoria, preco_min, preco_max


def validar_novo_usuario(dados):
    dados = _exigir_dict(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not all(isinstance(v, str) for v in (nome, email, senha)):
        raise ApiError({"erro": MSG_DADOS_INVALIDOS}, 400)
    if not nome or not email or not senha:
        raise ApiError({"erro": "Nome, email e senha são obrigatórios"}, 400)
    return nome, email, senha


def validar_login(dados):
    mensagem = "Email e senha são obrigatórios"
    if not isinstance(dados, dict):
        raise ApiError({"erro": mensagem}, 400)
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not isinstance(email, str) or not isinstance(senha, str) or not email or not senha:
        raise ApiError({"erro": mensagem}, 400)
    return email, senha


def validar_pedido(dados):
    dados = _exigir_dict(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ApiError({"erro": "Usuario ID é obrigatório"}, 400)
    if not itens:
        raise ApiError({"erro": "Pedido deve ter pelo menos 1 item"}, 400)

    if not _eh_inteiro(usuario_id) or not isinstance(itens, list):
        raise ApiError({"erro": MSG_DADOS_INVALIDOS}, 400)
    for item in itens:
        if not isinstance(item, dict):
            raise ApiError({"erro": MSG_DADOS_INVALIDOS}, 400)
        produto_id = item.get("produto_id")
        quantidade = item.get("quantidade")
        if not _eh_inteiro(produto_id) or not _eh_inteiro(quantidade) or quantidade <= 0:
            raise ApiError({"erro": MSG_DADOS_INVALIDOS}, 400)
    return usuario_id, itens


def validar_status(dados):
    if not isinstance(dados, dict):
        raise ApiError({"erro": "Status inválido"}, 400)
    novo_status = dados.get("status", "")
    if not isinstance(novo_status, str) or novo_status not in constants.STATUS_VALIDOS:
        raise ApiError({"erro": "Status inválido"}, 400)
    return novo_status


def validar_query_admin(dados):
    consulta = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not consulta or not isinstance(consulta, str):
        raise ApiError({"erro": "Query não informada"}, 400)
    return consulta
