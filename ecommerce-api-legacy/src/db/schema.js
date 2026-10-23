const { PAYMENT_STATUS, COURSE_ACTIVE } = require('../config/constants');

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };

async function initSchema(db, passwordHasher) {
    await db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await db.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await db.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await db.run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
    await db.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

    await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [SEED_USER.name, SEED_USER.email, passwordHasher.hash(SEED_USER.password)],
    );
    await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
        ['Clean Architecture', 997.0, COURSE_ACTIVE, 'Docker', 497.0, COURSE_ACTIVE],
    );
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [1, 997.0, PAYMENT_STATUS.PAID],
    );
}

module.exports = { initSchema };
