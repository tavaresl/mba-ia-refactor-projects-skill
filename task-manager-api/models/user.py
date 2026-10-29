import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import DEFAULT_ROLE
from models.db import db
from utils.dates import utc_now

LEGACY_MD5_HASH = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        """Nunca inclui a senha nem o hash."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Aceita hashes MD5 legados e os regrava no formato novo quando corretos.

        Quem chama deve fazer commit se `self.password` mudou.
        """
        if LEGACY_MD5_HASH.match(self.password or ''):
            legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
            if not hmac.compare_digest(self.password, legacy_hash):
                return False
            self.set_password(raw_password)
            return True
        return check_password_hash(self.password, raw_password)
