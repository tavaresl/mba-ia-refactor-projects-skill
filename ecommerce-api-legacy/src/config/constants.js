const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Cartões que começam com este prefixo são aprovados pelo gateway.
const APPROVED_CARD_PREFIX = '4';

const COURSE_ACTIVE = 1;

const DB_FILENAME = ':memory:';

const DEFAULT_PORT = 3000;

const ADMIN_TOKEN_HEADER = 'X-Admin-Token';

module.exports = {
    PAYMENT_STATUS,
    APPROVED_CARD_PREFIX,
    COURSE_ACTIVE,
    DB_FILENAME,
    DEFAULT_PORT,
    ADMIN_TOKEN_HEADER,
};
