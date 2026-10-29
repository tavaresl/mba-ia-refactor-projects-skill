const DEFAULT_PORT = 3000;
const DEFAULT_LOG_LEVEL = 'info';

const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Gateway simulado: cartões que começam com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';
const COURSE_ACTIVE = 1;

const ADMIN_TOKEN_HEADER = 'X-Admin-Token';

const SCRYPT = Object.freeze({ SALT_BYTES: 16, KEY_LENGTH: 64, PREFIX: 'scrypt' });

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+$/;
const POSITIVE_INTEGER_PATTERN = /^[1-9][0-9]*$/;

// Textos do contrato externo (palavra por palavra do original).
const MESSAGES = Object.freeze({
    BAD_REQUEST: 'Bad Request',
    COURSE_NOT_FOUND: 'Curso não encontrado',
    PAYMENT_DENIED: 'Pagamento recusado',
    DB_ERROR: 'Erro DB',
    USER_CREATE_ERROR: 'Erro ao criar usuário',
    ENROLLMENT_ERROR: 'Erro Matrícula',
    PAYMENT_ERROR: 'Erro Pagamento',
    CHECKOUT_SUCCESS: 'Sucesso',
    USER_DELETED: 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.',
    USER_NOT_FOUND: 'Usuário não encontrado',
    FORBIDDEN: 'Acesso negado',
    INTERNAL_ERROR: 'Internal Server Error',
    UNKNOWN_STUDENT: 'Unknown',
});

module.exports = {
    DEFAULT_PORT,
    DEFAULT_LOG_LEVEL,
    PAYMENT_STATUS,
    APPROVED_CARD_PREFIX,
    COURSE_ACTIVE,
    ADMIN_TOKEN_HEADER,
    SCRYPT,
    EMAIL_PATTERN,
    POSITIVE_INTEGER_PATTERN,
    MESSAGES,
};
