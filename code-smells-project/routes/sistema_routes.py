from flask import Blueprint, current_app

from controllers import sistema_controller
from db.connection import get_db
from routes._http import responder

bp = Blueprint("sistema", __name__)


@bp.get("/")
def index():
    return responder(sistema_controller.index())


@bp.get("/health")
def health_check():
    return responder(sistema_controller.health(get_db(), current_app.config["APP_ENV"]))
