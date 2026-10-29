const express = require('express');
const config = require('./config');
const { createLogger } = require('./config/logger');
const { createDatabase } = require('./db/connection');
const { initSchema } = require('./db/schema');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createPaymentModel } = require('./models/paymentModel');
const { createAuditLogModel } = require('./models/auditLogModel');
const { createPasswordHasher } = require('./services/passwordHasher');
const { createPaymentGateway } = require('./services/paymentGateway');
const { createCheckoutService } = require('./services/checkoutService');
const { createFinancialReportService } = require('./services/financialReportService');
const { createUserService } = require('./services/userService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createAdminAuth } = require('./middlewares/adminAuth');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { createRoutes } = require('./routes');

// Composition root: único lugar que conhece todas as peças.
async function main() {
    const logger = createLogger(config.logLevel);
    const passwordHasher = createPasswordHasher();
    const db = createDatabase();
    await initSchema(db, passwordHasher);

    const userModel = createUserModel(db);
    const courseModel = createCourseModel(db);
    const enrollmentModel = createEnrollmentModel(db);
    const paymentModel = createPaymentModel(db);
    const auditLogModel = createAuditLogModel(db);

    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey, logger });
    const checkoutService = createCheckoutService({
        db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
        paymentGateway, passwordHasher, logger,
    });
    const financialReportService = createFinancialReportService({ courseModel, enrollmentModel, logger });
    const userService = createUserService({ userModel, logger });

    const app = express();
    app.use(express.json());
    app.use('/api', createRoutes({
        checkoutController: createCheckoutController({ checkoutService }),
        reportController: createReportController({ financialReportService }),
        userController: createUserController({ userService }),
        adminRequired: createAdminAuth({ adminToken: config.adminToken }),
    }));
    app.use(createErrorHandler({ logger }));

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    console.error('Falha ao iniciar a aplicação:', err);
    process.exit(1);
});
