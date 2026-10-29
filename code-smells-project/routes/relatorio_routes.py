from flask import Blueprint

from controllers import relatorio_controller
from db.connection import get_db
from routes._http import responder

bp = Blueprint("relatorios", __name__)


@bp.get("/relatorios/vendas")
def relatorio_vendas():
    return responder(relatorio_controller.vendas(get_db()))
