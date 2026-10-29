"""Hash e verificação de senhas."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def gerar_hash(senha):
    return generate_password_hash(senha)


def eh_hash(valor):
    return isinstance(valor, str) and valor.startswith(PREFIXOS_HASH)


def verificar_senha(armazenada, senha):
    """Retorna (senha_confere, precisa_regravar_como_hash).

    Aceita senha legada em texto puro (compat. com bancos antigos) e pede o rehash.
    """
    if eh_hash(armazenada):
        return check_password_hash(armazenada, senha), False
    if armazenada is None:
        return False, False
    return hmac.compare_digest(armazenada.encode(), senha.encode()), True
