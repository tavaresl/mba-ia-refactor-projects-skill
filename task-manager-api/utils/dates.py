from datetime import datetime, timezone

from config.constants import DATE_FORMAT


def utc_now():
    """Agora em UTC como datetime sem fuso (mesmo formato gravado antes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(value):
    """Converte 'YYYY-MM-DD'. Levanta ValueError/TypeError se inválido."""
    return datetime.strptime(value, DATE_FORMAT)
