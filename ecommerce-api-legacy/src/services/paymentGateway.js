const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

const maskCard = (cardNumber) => `****${String(cardNumber).slice(-4)}`;

// Gateway simulado. A chave fica só aqui dentro e nunca é logada.
function createPaymentGateway({ apiKey, logger }) {
    return {
        charge({ cardNumber }) {
            logger.info(`Processando cartão ${maskCard(cardNumber)}`);
            logger.debug(`Gateway ${apiKey ? 'configurado' : 'sem chave configurada'}`);
            return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { createPaymentGateway };
