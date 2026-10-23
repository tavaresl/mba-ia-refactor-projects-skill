// Encaminha rejeições de handlers async para o error handler central.
module.exports = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};
