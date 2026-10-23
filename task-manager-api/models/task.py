from sqlalchemy import case, func, select
from sqlalchemy.orm import selectinload

from models.database import db, utc_now

TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
FINISHED_STATUSES = ('done', 'cancelled')
DEFAULT_STATUS = 'pending'
DEFAULT_PRIORITY = 3
PRIORITY_MIN = 1
PRIORITY_MAX = 5
HIGH_PRIORITY_MAX = 2
TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self):
        if not self.due_date or self.due_date >= utc_now():
            return False
        return self.status not in FINISHED_STATUSES

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

    def to_detail_dict(self):
        data = self.to_dict()
        data['overdue'] = self.is_overdue()
        return data

    def to_listing_dict(self):
        data = self.to_detail_dict()
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    @staticmethod
    def find_by_id(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def list_all():
        return db.session.execute(select(Task)).scalars().all()

    @staticmethod
    def list_all_with_relations():
        query = select(Task).options(selectinload(Task.user), selectinload(Task.category))
        return db.session.execute(query).scalars().all()

    @staticmethod
    def list_for_user(user_id):
        return db.session.execute(select(Task).filter_by(user_id=user_id)).scalars().all()

    @staticmethod
    def search(text, status, priority, user_id):
        query = select(Task)
        if text:
            query = query.where(db.or_(
                Task.title.like(f'%{text}%'),
                Task.description.like(f'%{text}%'),
            ))
        if status:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        return db.session.execute(query).scalars().all()

    @staticmethod
    def count_all():
        return db.session.scalar(select(func.count()).select_from(Task))

    @staticmethod
    def count_grouped(column):
        """Contagem de tasks agrupada por uma coluna: {valor: quantidade}."""
        rows = db.session.execute(select(column, func.count()).group_by(column)).all()
        return {value: total for value, total in rows}

    @staticmethod
    def totals_by_user():
        """{user_id: (total de tasks, tasks concluídas)} em uma única consulta."""
        done = func.sum(case((Task.status == 'done', 1), else_=0))
        query = (select(Task.user_id, func.count(), done)
                 .where(Task.user_id.isnot(None))
                 .group_by(Task.user_id))
        return {user_id: (total, int(completed))
                for user_id, total, completed in db.session.execute(query).all()}

    @staticmethod
    def count_created_since(moment):
        query = select(func.count()).select_from(Task).where(Task.created_at >= moment)
        return db.session.scalar(query)

    @staticmethod
    def count_done_updated_since(moment):
        query = (select(func.count()).select_from(Task)
                 .where(Task.status == 'done', Task.updated_at >= moment))
        return db.session.scalar(query)
