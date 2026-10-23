class AuditLogModel {
    constructor(db) {
        this.db = db;
    }

    async create(action, executor = this.db) {
        const { lastID } = await executor.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
        );
        return lastID;
    }
}

module.exports = AuditLogModel;
