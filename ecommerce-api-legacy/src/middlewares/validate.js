// Aplica um validator (função pura) e deixa o resultado em req.input.
const validate = (validator, source = 'body') => (req, res, next) => {
    try {
        req.input = validator(req[source]);
        next();
    } catch (err) {
        next(err);
    }
};

module.exports = validate;
