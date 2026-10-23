from flask import Blueprint

from controllers import admin_controller as c
from middlewares.admin_auth import admin_required

bp = Blueprint("admin", __name__)

bp.add_url_rule("/admin/reset-db", "reset_database", admin_required(c.reset_database), methods=["POST"])
bp.add_url_rule("/admin/query", "executar_query", admin_required(c.executar_query), methods=["POST"])
