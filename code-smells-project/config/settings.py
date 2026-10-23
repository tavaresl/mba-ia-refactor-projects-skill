"""Configuração lida de variáveis de ambiente, com defaults seguros."""
import os
import secrets

from config import constants

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _as_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def load_settings():
    db_path = os.environ.get("DB_PATH", constants.DEFAULT_DB_PATH)
    db_file = db_path if os.path.isabs(db_path) else os.path.join(BASE_DIR, db_path)
    return {
        # Sem sessões na aplicação: sem SECRET_KEY no ambiente, gera uma chave só para este processo.
        "SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        "DEBUG": _as_bool(os.environ.get("DEBUG"), default=False),
        "HOST": os.environ.get("HOST", constants.DEFAULT_HOST),
        "PORT": int(os.environ.get("PORT", constants.DEFAULT_PORT)),
        "DB_PATH": db_path,
        "DB_FILE": db_file,
        "ADMIN_TOKEN": os.environ.get("ADMIN_TOKEN", ""),
        "APP_ENV": os.environ.get("APP_ENV", constants.DEFAULT_APP_ENV),
    }
