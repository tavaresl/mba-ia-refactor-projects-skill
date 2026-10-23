"""Composition root: monta config, banco, middlewares e rotas."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from db.connection import close_db
from db.schema import init_db
from middlewares.errors import register_error_handlers
from routes import register_routes

logger = logging.getLogger(__name__)


def create_app():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.update(load_settings())
    CORS(app)

    init_db(app.config["DB_FILE"])
    app.teardown_appcontext(close_db)
    register_error_handlers(app)
    register_routes(app)
    return app


app = create_app()

if __name__ == "__main__":
    logger.info("SERVIDOR INICIADO em http://%s:%s", app.config["HOST"], app.config["PORT"])
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
