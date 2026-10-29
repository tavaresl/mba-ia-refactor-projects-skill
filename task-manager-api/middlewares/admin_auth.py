"""Credencial de administrador (X-Admin-Token × ADMIN_TOKEN do ambiente)."""
import hmac

from flask import current_app, request

from config.constants import ADMIN_TOKEN_HEADER


def has_admin_token():
    expected = current_app.config.get('ADMIN_TOKEN') or ''
    received = request.headers.get(ADMIN_TOKEN_HEADER, '')
    return bool(expected) and hmac.compare_digest(expected.encode(), received.encode())
