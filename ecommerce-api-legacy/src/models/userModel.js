function createUserModel(db) {
    return {
        findByEmail: (email) => db.get('SELECT id FROM users WHERE email = ?', [email]),

        async create({ name, email, passwordHash }, executor = db) {
            const { lastID } = await executor.run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, passwordHash],
            );
            return lastID;
        },

        async deleteById(id) {
            const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes;
        },
    };
}

module.exports = { createUserModel };
