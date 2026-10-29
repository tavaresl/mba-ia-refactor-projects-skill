from sqlalchemy import and_, or_

from config.constants import CLOSED_TASK_STATUSES, DEFAULT_PRIORITY, TASK_STATUS_PENDING
from models.db import db
from utils.dates import utc_now


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=TASK_STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_user_task_dict(self, now=None):
        """Subconjunto usado em GET /users/<id>/tasks."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(now),
        }

    def is_overdue(self, now=None):
        if not self.due_date:
            return False
        now = now or utc_now()
        return self.due_date < now and self.status not in CLOSED_TASK_STATUSES

    @classmethod
    def overdue_filter(cls, now):
        """Mesma regra de is_overdue, para uso em consultas SQL."""
        return and_(
            cls.due_date.isnot(None),
            cls.due_date < now,
            or_(cls.status.is_(None), cls.status.not_in(CLOSED_TASK_STATUSES)),
        )
