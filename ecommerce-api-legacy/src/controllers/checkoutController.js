const { MESSAGES } = require('../config/constants');

function createCheckoutController({ checkoutService }) {
    return {
        async create(req, res) {
            const { enrollmentId } = await checkoutService.checkout(req.input);
            res.status(200).json({ msg: MESSAGES.CHECKOUT_SUCCESS, enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
