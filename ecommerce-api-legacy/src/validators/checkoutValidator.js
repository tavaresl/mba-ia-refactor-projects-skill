const AppError = require('../exceptions/AppError');
const { EMAIL_PATTERN, POSITIVE_INTEGER_PATTERN, MESSAGES } = require('../config/constants');

const badRequest = () => new AppError(400, MESSAGES.BAD_REQUEST);
const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

function parseCourseId(value) {
    if (typeof value === 'number' && Number.isInteger(value) && value > 0) return value;
    if (typeof value === 'string' && POSITIVE_INTEGER_PATTERN.test(value)) return Number(value);
    return null;
}

// Campos externos (usr, eml, pwd, c_id, card) viram nomes descritivos aqui.
function validateCheckout(body) {
    if (!body || typeof body !== 'object' || Array.isArray(body)) throw badRequest();

    const { usr, eml, pwd, c_id: rawCourseId, card } = body;
    const courseId = parseCourseId(rawCourseId);

    if (!isNonEmptyString(usr) || !isNonEmptyString(eml) || !isNonEmptyString(card)) throw badRequest();
    if (courseId === null) throw badRequest();
    if (!EMAIL_PATTERN.test(eml)) throw badRequest();
    if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') throw badRequest();

    return { name: usr, email: eml, password: pwd || '', courseId, cardNumber: card };
}

module.exports = { validateCheckout };
