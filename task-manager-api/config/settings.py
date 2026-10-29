"""Configuração lida do ambiente (e do .env na raiz do projeto)."""
import os

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _as_bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    """Segredos não têm default: vêm só do ambiente."""

    def __init__(self):
        load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
        env = os.environ
        self.SECRET_KEY = env.get('SECRET_KEY') or None
        self.ADMIN_TOKEN = env.get('ADMIN_TOKEN') or ''
        self.DATABASE_URL = env.get('DATABASE_URL') or 'sqlite:///tasks.db'
        self.DEBUG = _as_bool(env.get('DEBUG', 'false'))
        self.HOST = env.get('HOST') or '0.0.0.0'
        self.PORT = int(env.get('PORT') or 5000)
        self.SMTP_HOST = env.get('SMTP_HOST') or 'smtp.gmail.com'
        self.SMTP_PORT = int(env.get('SMTP_PORT') or 587)
        self.SMTP_USER = env.get('SMTP_USER') or ''
        self.SMTP_PASSWORD = env.get('SMTP_PASSWORD') or ''
