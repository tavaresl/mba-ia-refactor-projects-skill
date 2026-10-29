"""Utilitários HTTP compartilhados pelas rotas."""
from flask import jsonify, request


def corpo_json():
    """Corpo JSON ou None se ausente/malformado (o validator decide o erro)."""
    return request.get_json(silent=True)


def responder(resultado):
    corpo, status = resultado
    return jsonify(corpo), status
