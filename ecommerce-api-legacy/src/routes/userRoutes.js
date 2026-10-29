const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const validate = require('../middlewares/validate');
const { validateUserId } = require('../validators/userValidator');

function createUserRoutes({ userController, adminRequired }) {
    const router = Router();
    router.delete('/users/:id', adminRequired, validate(validateUserId, 'params'), asyncHandler(userController.remove));
    return router;
}

module.exports = { createUserRoutes };
