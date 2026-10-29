const { COURSE_ACTIVE } = require('../config/constants');

function createCourseModel(db) {
    return {
        findActiveById: (id) => db.get('SELECT * FROM courses WHERE id = ? AND active = ?', [id, COURSE_ACTIVE]),
        findAll: () => db.all('SELECT * FROM courses ORDER BY id'),
    };
}

module.exports = { createCourseModel };
