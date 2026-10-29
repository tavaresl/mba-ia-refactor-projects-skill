import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from middlewares.errors import register_error_handlers
from models import db, init_db
from routes import register_routes
from services.notification_service import NotificationService


def create_app(settings=None):
    """Composition root: monta config, banco, CORS, erros, rotas e serviços."""
    settings = settings or Settings()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={'hide_parameters': True},
        SECRET_KEY=settings.SECRET_KEY,
        ADMIN_TOKEN=settings.ADMIN_TOKEN,
        DEBUG=settings.DEBUG,
        HOST=settings.HOST,
        PORT=settings.PORT,
    )
    if not settings.SECRET_KEY:
        app.logger.warning('SECRET_KEY não configurada no ambiente')

    CORS(app)
    db.init_app(app)
    register_error_handlers(app)
    register_routes(app)
    app.extensions['notification_service'] = NotificationService.from_settings(settings)
    init_db(app)
    return app


app = create_app()

if __name__ == '__main__':
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT'],
    )
