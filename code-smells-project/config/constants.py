"""Constantes de negócio e de aplicação (sem segredos)."""

APP_VERSION = "1.0.0"
DEFAULT_PORT = 5000
DEFAULT_HOST = "0.0.0.0"
DEFAULT_DB_PATH = "loja.db"
DEFAULT_APP_ENV = "producao"

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO]

NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# Faixas de desconto do relatório: (faturamento acima de, taxa), da maior para a menor.
FAIXAS_DESCONTO = [
    (10_000, 0.10),
    (5_000, 0.05),
    (1_000, 0.02),
]

TIPO_USUARIO_PADRAO = "cliente"
