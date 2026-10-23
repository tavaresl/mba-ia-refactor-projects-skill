const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

const VISIBLE_DIGITS = 4;

class PaymentGateway {
    constructor({ apiKey, logger }) {
        this.apiKey = apiKey;
        this.logger = logger;
    }

    charge(cardNumber) {
        const lastDigits = cardNumber.slice(-VISIBLE_DIGITS);
        this.logger.info(`Processando cartão final ${lastDigits} (gateway ${this.apiKey ? 'configurado' : 'sem chave'})`);
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = PaymentGateway;
