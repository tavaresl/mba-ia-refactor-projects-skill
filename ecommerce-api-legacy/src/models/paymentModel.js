class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ enrollmentId, amount, status }, executor = this.db) {
        const { lastID } = await executor.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status],
        );
        return lastID;
    }
}

module.exports = PaymentModel;
