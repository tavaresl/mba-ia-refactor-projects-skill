from services import relatorio_service


def vendas(conn):
    return {"dados": relatorio_service.relatorio_vendas(conn), "sucesso": True}, 200
