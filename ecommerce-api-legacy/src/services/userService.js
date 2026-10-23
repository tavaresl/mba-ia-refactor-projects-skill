const AppError = require('../middlewares/appError');

class UserService {
    constructor({ db, userModel }) {
        this.db = db;
        this.userModel = userModel;
    }

    // Remove apenas o usuário; matrículas e pagamentos são preservados (histórico financeiro).
    async deleteUser(id) {
        const removed = await this.db.transaction((tx) => this.userModel.deleteById(id, tx));
        if (removed === 0) throw new AppError(404, 'Usuário não encontrado');
    }
}

module.exports = UserService;
