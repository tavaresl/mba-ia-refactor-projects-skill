const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function createAdminRoutes({ reportController, adminRequired }) {
    const router = Router();
    router.get('/admin/financial-report', adminRequired, asyncHandler(reportController.financial));
    return router;
}

module.exports = { createAdminRoutes };
