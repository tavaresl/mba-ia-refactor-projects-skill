"""Hash e verificação de senha (werkzeug.security) com migração de senhas legadas."""
import hmac
import logging
import re

from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

_HASH_FORMAT = re.compile(r"^(scrypt|pbkdf2):[^$]*\$[^$]+\$[0-9a-f]+$")


def is_hashed(valor):
    return bool(valor) and _HASH_FORMAT.match(valor) is not None


def hash_senha(senha):
    return generate_password_hash(senha)


def _senha_confere(armazenada, informada):
    """Retorna (confere, precisa_rehash)."""
    if is_hashed(armazenada):
        return check_password_hash(armazenada, informada), False
    # legado em texto puro: aceita uma vez e regrava com hash
    confere = hmac.compare_digest((armazenada or "").encode("utf-8"), informada.encode("utf-8"))
    return confere, confere


def autenticar(email, senha):
    from models import usuario_model  # import local: evita ciclo db.schema -> auth_service -> models

    for row in usuario_model.buscar_rows_por_email(email):
        confere, rehash = _senha_confere(row["senha"], senha)
        if confere:
            if rehash:
                usuario_model.atualizar_senha(row["id"], hash_senha(senha))
            return usuario_model.resumo_login(row)
    return None
