"""Autenticação dos endpoints administrativos (ADMIN_TOKEN + header X-Admin-Token)."""
import hmac
from functools import wraps

from flask import current_app, request

from middlewares.errors import ApiError


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN", "")
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(esperado.encode(), recebido.encode()):
            raise ApiError("Acesso negado", 403)
        return view(*args, **kwargs)

    return wrapper
