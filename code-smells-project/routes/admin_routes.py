from flask import Blueprint, current_app

from controllers import admin_controller
from db.connection import get_db
from middlewares.admin_auth import admin_required
from routes._http import corpo_json, responder

bp = Blueprint("admin", __name__)


@bp.post("/admin/reset-db")
@admin_required
def reset_database():
    return responder(admin_controller.resetar_banco(get_db()))


@bp.post("/admin/query")
@admin_required
def executar_query():
    return responder(admin_controller.executar_query(current_app.config["DB_PATH"], corpo_json()))
