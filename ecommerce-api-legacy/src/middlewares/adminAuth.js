const crypto = require('crypto');
const { ADMIN_TOKEN_HEADER } = require('../config/constants');

const digest = (value) => crypto.createHash('sha256').update(String(value)).digest();

// Rotas administrativas ficam desligadas (403) até que ADMIN_TOKEN seja configurado.
function createAdminAuth(adminToken) {
    return (req, res, next) => {
        const received = req.get(ADMIN_TOKEN_HEADER) || '';
        const authorized = adminToken !== '' && crypto.timingSafeEqual(digest(received), digest(adminToken));
        if (!authorized) return res.status(403).send('Acesso negado');
        return next();
    };
}

module.exports = { createAdminAuth };
