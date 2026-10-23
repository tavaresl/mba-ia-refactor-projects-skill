const express = require('express');
const { loadConfig } = require('./config');
const { DB_FILENAME } = require('./config/constants');
const { createLogger } = require('./utils/logger');
const { createDatabase } = require('./db/connection');
const { initSchema } = require('./db/schema');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const PasswordHasher = require('./services/passwordHasher');
const PaymentGateway = require('./services/paymentGateway');
const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');
const UserService = require('./services/userService');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const { createAdminAuth } = require('./middlewares/adminAuth');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { registerRoutes } = require('./routes');

// Composition root: único ponto que conhece todas as peças.
async function main() {
    const config = loadConfig();
    const logger = createLogger(config.logLevel);

    const db = createDatabase(DB_FILENAME);
    const passwordHasher = new PasswordHasher();
    await initSchema(db, passwordHasher);

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);

    const checkoutService = new CheckoutService({
        db,
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        passwordHasher,
        paymentGateway: new PaymentGateway({ apiKey: config.paymentGatewayKey, logger }),
        cache: new Map(),
        logger,
    });
    const reportService = new ReportService({ courseModel, enrollmentModel });
    const userService = new UserService({ db, userModel });

    const app = express();
    app.use(express.json());
    registerRoutes(app, {
        checkoutController: new CheckoutController(checkoutService),
        reportController: new ReportController(reportService),
        userController: new UserController(userService),
        adminAuth: createAdminAuth(config.adminToken),
    });
    app.use(createErrorHandler(logger));

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    process.stderr.write(`Falha ao iniciar a aplicação: ${err.stack || err}\n`);
    process.exit(1);
});
