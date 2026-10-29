const AppError = require('../exceptions/AppError');
const { POSITIVE_INTEGER_PATTERN, MESSAGES } = require('../config/constants');

function validateUserId(params) {
    const { id } = params || {};
    if (typeof id !== 'string' || !POSITIVE_INTEGER_PATTERN.test(id)) {
        throw new AppError(400, MESSAGES.BAD_REQUEST);
    }
    return { id: Number(id) };
}

module.exports = { validateUserId };
