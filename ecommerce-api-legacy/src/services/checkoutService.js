const AppError = require('../exceptions/AppError');
const { PAYMENT_STATUS, MESSAGES } = require('../config/constants');

function createCheckoutService({
    db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
    paymentGateway, passwordHasher, logger,
}) {
    // Executa uma etapa de banco; falha vira AppError com a mensagem original da etapa.
    async function step(work, status, message) {
        try {
            return await work();
        } catch (err) {
            if (err instanceof AppError) throw err;
            logger.error(`${message}: ${err.message}`);
            throw new AppError(status, message);
        }
    }

    async function checkout({ name, email, password, courseId, cardNumber }) {
        // Falha de banco aqui sempre respondeu 404 no original (mantido).
        const course = await step(() => courseModel.findActiveById(courseId), 404, MESSAGES.COURSE_NOT_FOUND);
        if (!course) throw new AppError(404, MESSAGES.COURSE_NOT_FOUND);

        const existingUser = await step(() => userModel.findByEmail(email), 500, MESSAGES.DB_ERROR);
        if (!existingUser && !password) throw new AppError(400, MESSAGES.BAD_REQUEST);

        // Pagamento decidido antes de qualquer escrita: recusa não grava nada.
        const status = paymentGateway.charge({ cardNumber });
        if (status === PAYMENT_STATUS.DENIED) throw new AppError(400, MESSAGES.PAYMENT_DENIED);

        const passwordHash = existingUser ? null : await passwordHasher.hash(password);

        const { userId, enrollmentId } = await db.transaction(async (tx) => {
            const ownerId = existingUser
                ? existingUser.id
                : await step(() => userModel.create({ name, email, passwordHash }, tx), 500, MESSAGES.USER_CREATE_ERROR);
            const newEnrollmentId = await step(
                () => enrollmentModel.create({ userId: ownerId, courseId }, tx), 500, MESSAGES.ENROLLMENT_ERROR,
            );
            await step(
                () => paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status }, tx),
                500, MESSAGES.PAYMENT_ERROR,
            );
            return { userId: ownerId, enrollmentId: newEnrollmentId };
        });

        try {
            await auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);
        } catch (err) {
            logger.error(`Falha ao gravar auditoria do checkout: ${err.message}`);
        }
        logger.info(`Checkout concluído: curso ${courseId}, usuário ${userId}`);

        return { enrollmentId };
    }

    return { checkout };
}

module.exports = { createCheckoutService };
