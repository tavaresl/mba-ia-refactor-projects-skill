const { DEFAULT_PORT } = require('./constants');

function loadConfig(env = process.env) {
    return {
        port: Number(env.PORT) || DEFAULT_PORT,
        paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || '',
        adminToken: env.ADMIN_TOKEN || '',
        logLevel: env.LOG_LEVEL || 'info',
    };
}

module.exports = { loadConfig };
