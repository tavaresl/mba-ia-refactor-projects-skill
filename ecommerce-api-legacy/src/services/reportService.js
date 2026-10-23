const { PAYMENT_STATUS } = require('../config/constants');

const UNKNOWN_STUDENT = 'Unknown';

class ReportService {
    constructor({ courseModel, enrollmentModel }) {
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
    }

    async financialReport() {
        const [courses, rows] = await Promise.all([
            this.courseModel.findAll(),
            this.enrollmentModel.findReportRows(),
        ]);

        const report = courses.map((course) => {
            const students = [];
            let revenue = 0;
            rows.filter((row) => row.course_id === course.id).forEach((row) => {
                if (row.status === PAYMENT_STATUS.PAID) revenue += row.amount;
                students.push({
                    student: row.user_name || UNKNOWN_STUDENT,
                    paid: row.amount === null || row.amount === undefined ? 0 : row.amount,
                });
            });
            return { course: course.title, revenue, students };
        });

        // Ordem do contrato original: cursos sem matrículas primeiro, depois os demais.
        return [
            ...report.filter((entry) => entry.students.length === 0),
            ...report.filter((entry) => entry.students.length > 0),
        ];
    }
}

module.exports = ReportService;
