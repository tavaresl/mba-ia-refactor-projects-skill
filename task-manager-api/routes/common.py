from flask import request
from werkzeug.exceptions import BadRequest

from middlewares.errors import ApiError


def read_json():
    """Corpo JSON da requisição; JSON malformado vira 400 no formato da API."""
    try:
        return request.get_json()
    except BadRequest:
        raise ApiError('Dados inválidos', 400)
