import hashlib
import hmac
import re

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from werkzeug.security import check_password_hash, generate_password_hash

from models.database import db, utc_now

USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
LEGACY_MD5_PATTERN = re.compile(r'^[0-9a-f]{32}$')


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
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def uses_legacy_hash(self):
        return bool(LEGACY_MD5_PATTERN.match(self.password or ''))

    def check_password(self, password):
        if self.uses_legacy_hash():
            legacy_digest = hashlib.md5(password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy_digest)
        return check_password_hash(self.password, password)

    @staticmethod
    def is_valid_email(email):
        return bool(EMAIL_PATTERN.match(email))

    @staticmethod
    def find_by_id(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def find_by_email(email):
        return db.session.execute(select(User).filter_by(email=email)).scalars().first()

    @staticmethod
    def list_all_with_tasks():
        query = select(User).options(selectinload(User.tasks))
        return db.session.execute(query).scalars().all()

    @staticmethod
    def list_all():
        return db.session.execute(select(User)).scalars().all()

    @staticmethod
    def count_all():
        return db.session.scalar(select(func.count()).select_from(User))
