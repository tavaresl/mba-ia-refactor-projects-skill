const http = require('http');
const AppError = require('./appError');

// Reproduz o formato original das respostas de erro: texto puro, sem stack trace.
function createErrorHandler(logger) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof AppError) {
            return res.status(err.status).send(err.message);
        }
        if (err.type === 'entity.parse.failed') {
            return res.status(400).send('Bad Request');
        }
        if (err.status >= 400 && err.status < 500) {
            return res.status(err.status).send(http.STATUS_CODES[err.status] || 'Bad Request');
        }
        logger.error('Erro não tratado', err);
        return res.status(500).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
