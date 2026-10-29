function createPaymentModel(db) {
    return {
        async create({ enrollmentId, amount, status }, executor = db) {
            const { lastID } = await executor.run(
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status],
            );
            return lastID;
        },
    };
}

module.exports = { createPaymentModel };
