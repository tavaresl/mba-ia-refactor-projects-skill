"""Proteção dos endpoints administrativos: desligados sem ADMIN_TOKEN configurado."""
import hmac
from functools import wraps

from flask import current_app, request

from middlewares.errors import ApiError


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN", "")
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(esperado.encode("utf-8"), recebido.encode("utf-8")):
            raise ApiError({"erro": "Acesso negado"}, 403)
        return view(*args, **kwargs)

    return wrapper
