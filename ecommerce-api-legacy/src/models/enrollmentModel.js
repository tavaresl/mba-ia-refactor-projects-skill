class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ userId, courseId }, executor = this.db) {
        const { lastID } = await executor.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
        );
        return lastID;
    }

    // Uma única query traz matrícula + aluno + pagamento (evita N+1).
    // O pagamento é o primeiro (menor id) de cada matrícula.
    findReportRows() {
        return this.db.all(`
            SELECT e.id AS enrollment_id,
                   e.course_id AS course_id,
                   u.name AS user_name,
                   p.amount AS amount,
                   p.status AS status
            FROM enrollments e
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.id = (
                SELECT MIN(id) FROM payments WHERE enrollment_id = e.id
            )
            ORDER BY e.id
        `);
    }
}

module.exports = EnrollmentModel;
