const checkoutRoutes = require('./checkoutRoutes');
const adminRoutes = require('./adminRoutes');
const userRoutes = require('./userRoutes');

function registerRoutes(app, { checkoutController, reportController, userController, adminAuth }) {
    app.use(checkoutRoutes(checkoutController));
    app.use(adminRoutes(reportController, adminAuth));
    app.use(userRoutes(userController, adminAuth));
}

module.exports = { registerRoutes };
