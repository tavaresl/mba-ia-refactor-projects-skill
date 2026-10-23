const { COURSE_ACTIVE } = require('../config/constants');

class CourseModel {
    constructor(db) {
        this.db = db;
    }

    findActiveById(id) {
        return this.db.get('SELECT * FROM courses WHERE id = ? AND active = ?', [id, COURSE_ACTIVE]);
    }

    findAll() {
        return this.db.all('SELECT * FROM courses ORDER BY id');
    }
}

module.exports = CourseModel;
