const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const validate = require('../middlewares/validate');
const { validateCheckout } = require('../validators/checkoutValidator');

function createCheckoutRoutes({ checkoutController }) {
    const router = Router();
    router.post('/checkout', validate(validateCheckout), asyncHandler(checkoutController.create));
    return router;
}

module.exports = { createCheckoutRoutes };
