"""Composition root: monta config, banco, middlewares e rotas."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from db import schema
from db.connection import conectar, fechar_db
from middlewares.errors import registrar_handlers
from routes import register_routes
from services import auth_service

logger = logging.getLogger(__name__)


def create_app(settings=None):
    settings = settings or load_settings()
    app = Flask(__name__)
    app.config.update(settings)
    CORS(app)

    registrar_handlers(app)
    app.teardown_appcontext(fechar_db)
    register_routes(app)

    conn = conectar(app.config["DB_PATH"])
    try:
        schema.inicializar(conn, auth_service.gerar_hash, auth_service.eh_hash)
    finally:
        conn.close()
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = create_app()

if __name__ == "__main__":
    logger.info("SERVIDOR INICIADO em http://localhost:%s", app.config["PORT"])
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
