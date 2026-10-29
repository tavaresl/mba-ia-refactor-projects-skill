function createEnrollmentModel(db) {
    return {
        async create({ userId, courseId }, executor = db) {
            const { lastID } = await executor.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId],
            );
            return lastID;
        },

        // Uma única query para o relatório (matrícula + aluno + primeiro pagamento).
        listForFinancialReport: () => db.all(`
            SELECT e.id AS enrollment_id,
                   e.course_id AS course_id,
                   u.id AS user_id,
                   u.name AS student_name,
                   p.amount AS payment_amount,
                   p.status AS payment_status
              FROM enrollments e
              LEFT JOIN users u ON u.id = e.user_id
              LEFT JOIN payments p ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
             ORDER BY e.id
        `),
    };
}

module.exports = { createEnrollmentModel };
