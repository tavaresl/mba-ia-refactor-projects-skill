from routes import admin_routes, pedido_routes, produto_routes, relatorio_routes, sistema_routes, usuario_routes


def register_routes(app):
    for modulo in (produto_routes, usuario_routes, pedido_routes, relatorio_routes, sistema_routes, admin_routes):
        app.register_blueprint(modulo.bp)
