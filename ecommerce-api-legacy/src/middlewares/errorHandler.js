const { STATUS_CODES } = require('http');
const AppError = require('../exceptions/AppError');
const { MESSAGES } = require('../config/constants');

// Respostas de erro seguem o formato original: texto puro, sem detalhe interno.
function createErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return function errorHandler(err, req, res, next) {
        if (res.headersSent) return next(err);

        if (err instanceof AppError) return res.status(err.status).send(err.message);

        if (err.type === 'entity.parse.failed') return res.status(400).send(MESSAGES.BAD_REQUEST);

        if (err.status >= 400 && err.status < 500) {
            return res.status(err.status).send(STATUS_CODES[err.status] || MESSAGES.BAD_REQUEST);
        }

        logger.error(`Erro não tratado em ${req.method} ${req.path}: ${err.stack || err}`);
        return res.status(500).send(MESSAGES.INTERNAL_ERROR);
    };
}

module.exports = { createErrorHandler };
