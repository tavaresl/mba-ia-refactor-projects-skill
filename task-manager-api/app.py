import logging

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  (registra os models no metadata)
from config.settings import Settings
from middlewares.errors import register_error_handlers
from models.database import db
from routes.category_routes import category_bp
from routes.main_routes import main_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService


def create_app(settings=None):
    settings = settings or Settings.from_env()
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key

    CORS(app)
    db.init_app(app)

    app.extensions['notification_service'] = NotificationService(
        settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password)

    for blueprint in (main_bp, task_bp, user_bp, category_bp, report_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
    return app


settings = Settings.from_env()
app = create_app(settings)

if __name__ == '__main__':
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
