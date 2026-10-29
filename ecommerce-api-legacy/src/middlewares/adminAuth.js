const crypto = require('crypto');
const AppError = require('../exceptions/AppError');
const { ADMIN_TOKEN_HEADER, MESSAGES } = require('../config/constants');

const digest = (value) => crypto.createHash('sha256').update(String(value)).digest();

// Rota desligada por padrão: sem ADMIN_TOKEN configurado, tudo é 403.
function createAdminAuth({ adminToken }) {
    return function adminRequired(req, res, next) {
        const received = req.get(ADMIN_TOKEN_HEADER) || '';
        const authorized = Boolean(adminToken) && crypto.timingSafeEqual(digest(received), digest(adminToken));
        if (!authorized) return next(new AppError(403, MESSAGES.FORBIDDEN));
        return next();
    };
}

module.exports = { createAdminAuth };
