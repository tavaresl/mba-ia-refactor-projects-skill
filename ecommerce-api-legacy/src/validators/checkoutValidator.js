const AppError = require('../middlewares/appError');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+$/;
const DIGITS_ONLY = /^\d+$/;

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

function parseCourseId(value) {
    if (typeof value === 'number' && Number.isInteger(value) && value >= 1) return value;
    if (typeof value === 'string' && DIGITS_ONLY.test(value) && Number(value) >= 1) return Number(value);
    return null;
}

// Os nomes do contrato externo (usr, eml, pwd, c_id, card) são traduzidos aqui.
function validateCheckout(req, res, next) {
    const body = req.body || {};
    const courseId = parseCourseId(body.c_id);
    const passwordInvalid = body.pwd !== undefined && body.pwd !== null && typeof body.pwd !== 'string';

    if (!isNonEmptyString(body.usr) || !isNonEmptyString(body.eml) || !isNonEmptyString(body.card)
        || !EMAIL_PATTERN.test(body.eml) || courseId === null || passwordInvalid) {
        return next(new AppError(400, 'Bad Request'));
    }

    req.checkoutInput = {
        name: body.usr,
        email: body.eml,
        password: body.pwd || '',
        courseId,
        cardNumber: body.card,
    };
    return next();
}

module.exports = { validateCheckout };
