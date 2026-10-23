const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const { validateCheckout } = require('../validators/checkoutValidator');

module.exports = (checkoutController) => {
    const router = Router();
    router.post('/api/checkout', validateCheckout, asyncHandler((req, res) => checkoutController.checkout(req, res)));
    return router;
};
