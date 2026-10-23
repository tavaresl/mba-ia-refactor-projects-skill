"""Relatório de vendas e regra de desconto por faixa de faturamento."""
from config import constants
from models import pedido_model


def calcular_desconto(faturamento):
    for faixa, taxa in constants.FAIXAS_DESCONTO:
        if faturamento > faixa:
            return faturamento * taxa
    return 0


def relatorio_vendas():
    totais = pedido_model.totais_para_relatorio()
    total_pedidos = totais["total_pedidos"]
    faturamento = totais["faturamento"]
    desconto = calcular_desconto(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": totais["pendentes"],
        "pedidos_aprovados": totais["aprovados"],
        "pedidos_cancelados": totais["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
