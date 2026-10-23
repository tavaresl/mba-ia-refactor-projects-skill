const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const { validateUserId } = require('../validators/idValidator');

module.exports = (userController, adminAuth) => {
    const router = Router();
    router.delete('/api/users/:id', adminAuth, validateUserId, asyncHandler((req, res) => userController.deleteUser(req, res)));
    return router;
};
