from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Cria as tabelas que ainda não existem."""
    with app.app_context():
        db.create_all()
