const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (reportController, adminAuth) => {
    const router = Router();
    router.get('/api/admin/financial-report', adminAuth, asyncHandler((req, res) => reportController.financialReport(req, res)));
    return router;
};
