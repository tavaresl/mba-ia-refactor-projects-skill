"""Configuração lida do ambiente (veja .env.example)."""
import os
import secrets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _caminho_db(valor):
    return valor if os.path.isabs(valor) else os.path.join(BASE_DIR, valor)


def load_settings():
    return {
        # Sem SECRET_KEY no ambiente, usa uma chave aleatória válida só para este boot.
        "SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        "DEBUG": os.environ.get("DEBUG", "false").lower() == "true",
        "HOST": os.environ.get("HOST", "0.0.0.0"),
        "PORT": int(os.environ.get("PORT", "5000")),
        "DB_PATH": _caminho_db(os.environ.get("DB_PATH", "loja.db")),
        "APP_ENV": os.environ.get("APP_ENV", "producao"),
        # Vazio = endpoints /admin/* desligados (403).
        "ADMIN_TOKEN": os.environ.get("ADMIN_TOKEN", ""),
    }
