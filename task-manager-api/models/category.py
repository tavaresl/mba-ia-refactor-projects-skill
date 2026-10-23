from sqlalchemy import func, select

from models.database import db, utc_now

DEFAULT_COLOR = '#000000'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @staticmethod
    def find_by_id(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def list_all():
        return db.session.execute(select(Category)).scalars().all()

    @staticmethod
    def count_all():
        return db.session.scalar(select(func.count()).select_from(Category))
