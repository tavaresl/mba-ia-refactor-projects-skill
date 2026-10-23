const AppError = require('../middlewares/appError');
const { PAYMENT_STATUS } = require('../config/constants');

async function orFail(promise, message, logger) {
    try {
        return await promise;
    } catch (err) {
        logger.error(message, err);
        throw new AppError(500, message);
    }
}

class CheckoutService {
    constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
        passwordHasher, paymentGateway, cache, logger }) {
        this.db = db;
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.passwordHasher = passwordHasher;
        this.paymentGateway = paymentGateway;
        this.cache = cache;
        this.logger = logger;
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        const course = await this.courseModel.findActiveById(courseId).catch(() => null);
        if (!course) throw new AppError(404, 'Curso não encontrado');

        // O pagamento é decidido antes de qualquer escrita: recusa não deixa registros.
        const status = this.paymentGateway.charge(cardNumber);
        if (status === PAYMENT_STATUS.DENIED) throw new AppError(400, 'Pagamento recusado');

        const { userId, enrollmentId } = await this.db.transaction(async (tx) => {
            const existing = await orFail(this.userModel.findByEmail(email, tx), 'Erro DB', this.logger);

            let id;
            if (existing) {
                id = existing.id;
            } else {
                if (!password) throw new AppError(400, 'Bad Request');
                const passwordHash = this.passwordHasher.hash(password);
                id = await orFail(
                    this.userModel.create({ name, email, passwordHash }, tx),
                    'Erro ao criar usuário',
                    this.logger,
                );
            }

            const newEnrollmentId = await orFail(
                this.enrollmentModel.create({ userId: id, courseId }, tx),
                'Erro Matrícula',
                this.logger,
            );
            await orFail(
                this.paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status }, tx),
                'Erro Pagamento',
                this.logger,
            );
            await this.auditLogModel.create(`Checkout curso ${courseId} por ${id}`, tx);

            return { userId: id, enrollmentId: newEnrollmentId };
        });

        this.cache.set(`last_checkout_${userId}`, course.title);
        this.logger.debug(`Salvando no cache: last_checkout_${userId}`);
        return { enrollmentId };
    }
}

module.exports = CheckoutService;
