"""Validação de forma/tipo dos payloads. Mensagens iguais às da API original."""
import math

from config.constants import (
    CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN, STATUS_PEDIDO_VALIDOS,
)
from middlewares.errors import ApiError


def _numero(valor):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
        return None
    return valor


def _inteiro(valor):
    """int, ou float de valor inteiro (ex.: 5.0); None para o resto (inclui bool)."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and math.isfinite(valor) and valor.is_integer():
        return int(valor)
    return None


def _exigir_objeto(dados, mensagem="Dados inválidos"):
    if not dados or not isinstance(dados, dict):
        raise ApiError(mensagem)


def validar_produto(dados):
    _exigir_objeto(dados)
    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise ApiError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if _numero(preco) is None:
        raise ApiError("Preço deve ser um número")
    if preco < 0:
        raise ApiError("Preço não pode ser negativo")
    estoque = _inteiro(estoque)
    if estoque is None:
        raise ApiError("Estoque deve ser um número inteiro")
    if estoque < 0:
        raise ApiError("Estoque não pode ser negativo")
    if not isinstance(nome, str):
        raise ApiError("Nome deve ser um texto")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ApiError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ApiError("Nome muito longo")
    if not isinstance(descricao, str):
        raise ApiError("Descrição deve ser um texto")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ApiError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtros_busca(args):
    filtros = {"termo": args.get("q", ""), "categoria": args.get("categoria", None)}
    for chave, parametro in (("preco_min", "preco_min"), ("preco_max", "preco_max")):
        bruto = args.get(parametro, None)
        filtros[chave] = None
        if bruto:
            try:
                valor = float(bruto)
            except ValueError:
                raise ApiError("Filtro de preço inválido")
            if not math.isfinite(valor):
                raise ApiError("Filtro de preço inválido")
            filtros[chave] = valor
    return filtros


def validar_usuario(dados):
    _exigir_objeto(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ApiError("Nome, email e senha são obrigatórios")
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        raise ApiError("Nome, email e senha devem ser texto")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    if not isinstance(dados, dict):
        dados = {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ApiError("Email e senha são obrigatórios")
    if not isinstance(email, str) or not isinstance(senha, str):
        raise ApiError("Email e senha devem ser texto")
    return {"email": email, "senha": senha}


def validar_pedido(dados):
    _exigir_objeto(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ApiError("Usuario ID é obrigatório")
    if not itens or len(itens) == 0:
        raise ApiError("Pedido deve ter pelo menos 1 item")

    usuario_id = _inteiro(usuario_id)
    if usuario_id is None:
        raise ApiError("Usuario ID inválido")
    if not isinstance(itens, list):
        raise ApiError("Itens do pedido inválidos")

    itens_validos = []
    for item in itens:
        if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
            raise ApiError("Itens do pedido inválidos")
        produto_id = _inteiro(item["produto_id"])
        if produto_id is None:
            raise ApiError("Itens do pedido inválidos")
        quantidade = _inteiro(item["quantidade"])
        if quantidade is None or quantidade <= 0:
            raise ApiError("Quantidade deve ser um número inteiro maior que zero")
        itens_validos.append({"produto_id": produto_id, "quantidade": quantidade})
    return {"usuario_id": usuario_id, "itens": itens_validos}


def validar_status_pedido(dados):
    if not isinstance(dados, dict):
        dados = {}
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ApiError("Status inválido")
    return novo_status


def validar_consulta_admin(dados):
    sql = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not sql or not isinstance(sql, str):
        raise ApiError("Query não informada")
    return sql
