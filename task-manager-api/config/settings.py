"""Configuração da aplicação, lida de variáveis de ambiente (e do .env local)."""
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DATABASE_URL = 'sqlite:///tasks.db'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
DEFAULT_SMTP_HOST = 'smtp.gmail.com'
DEFAULT_SMTP_PORT = 587


@dataclass(frozen=True)
class Settings:
    secret_key: str = field(repr=False)
    database_url: str
    debug: bool
    host: str
    port: int
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str = field(repr=False)

    @classmethod
    def from_env(cls):
        load_dotenv(PROJECT_ROOT / '.env')
        return cls(
            # Sem SECRET_KEY no ambiente, usa uma chave aleatória só desta execução.
            secret_key=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
            database_url=os.environ.get('DATABASE_URL', DEFAULT_DATABASE_URL),
            debug=os.environ.get('DEBUG', 'false').lower() == 'true',
            host=os.environ.get('HOST', DEFAULT_HOST),
            port=int(os.environ.get('PORT', DEFAULT_PORT)),
            smtp_host=os.environ.get('SMTP_HOST', DEFAULT_SMTP_HOST),
            smtp_port=int(os.environ.get('SMTP_PORT', DEFAULT_SMTP_PORT)),
            smtp_user=os.environ.get('SMTP_USER', ''),
            smtp_password=os.environ.get('SMTP_PASSWORD', ''),
        )
