const AppError = require('../exceptions/AppError');
const { PAYMENT_STATUS, MESSAGES } = require('../config/constants');

function createFinancialReportService({ courseModel, enrollmentModel, logger }) {
    async function build() {
        let courses;
        let rows;
        try {
            courses = await courseModel.findAll();
            rows = await enrollmentModel.listForFinancialReport();
        } catch (err) {
            logger.error(`Falha ao montar relatório financeiro: ${err.message}`);
            throw new AppError(500, MESSAGES.DB_ERROR);
        }

        const byCourse = new Map(courses.map((course) => [
            course.id,
            { course: course.title, revenue: 0, students: [] },
        ]));

        rows.forEach((row) => {
            const entry = byCourse.get(row.course_id);
            if (!entry) return;
            if (row.payment_status === PAYMENT_STATUS.PAID) entry.revenue += row.payment_amount;
            entry.students.push({
                student: row.user_id !== null ? row.student_name : MESSAGES.UNKNOWN_STUDENT,
                paid: row.payment_amount !== null ? row.payment_amount : 0,
            });
        });

        // Ordem do original: cursos sem matrícula primeiro, depois os demais (por id).
        const entries = [...byCourse.values()];
        return [
            ...entries.filter((entry) => entry.students.length === 0),
            ...entries.filter((entry) => entry.students.length > 0),
        ];
    }

    return { build };
}

module.exports = { createFinancialReportService };
