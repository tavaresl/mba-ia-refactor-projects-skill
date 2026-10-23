from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now():
    """Data/hora UTC sem fuso (mesmo formato que datetime.utcnow() gravava)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
