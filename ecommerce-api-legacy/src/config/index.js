const { DEFAULT_PORT, DEFAULT_LOG_LEVEL } = require('./constants');

// Segredos vêm só do ambiente (ver .env.example); sem valor padrão inseguro.
const config = Object.freeze({
    port: Number(process.env.PORT) || DEFAULT_PORT,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    adminToken: process.env.ADMIN_TOKEN || '',
    logLevel: process.env.LOG_LEVEL || DEFAULT_LOG_LEVEL,
});

module.exports = config;
