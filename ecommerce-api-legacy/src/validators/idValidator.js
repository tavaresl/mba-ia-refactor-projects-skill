const AppError = require('../middlewares/appError');

const DIGITS_ONLY = /^\d+$/;

function validateUserId(req, res, next) {
    if (!DIGITS_ONLY.test(req.params.id)) return next(new AppError(400, 'Bad Request'));
    req.userId = Number(req.params.id);
    return next();
}

module.exports = { validateUserId };
