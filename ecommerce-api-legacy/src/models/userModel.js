class UserModel {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email, executor = this.db) {
        return executor.get('SELECT id FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }, executor = this.db) {
        const { lastID } = await executor.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash],
        );
        return lastID;
    }

    async deleteById(id, executor = this.db) {
        const { changes } = await executor.run('DELETE FROM users WHERE id = ?', [id]);
        return changes;
    }
}

module.exports = UserModel;
