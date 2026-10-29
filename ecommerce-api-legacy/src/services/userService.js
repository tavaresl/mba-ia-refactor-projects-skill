const AppError = require('../exceptions/AppError');
const { MESSAGES } = require('../config/constants');

function createUserService({ userModel, logger }) {
    async function remove(id) {
        let changes = 1;
        try {
            changes = await userModel.deleteById(id);
        } catch (err) {
            // O original respondia sucesso mesmo com erro de banco (mantido, mas agora logado).
            logger.error(`Falha ao deletar usuário ${id}: ${err.message}`);
        }
        if (changes === 0) throw new AppError(404, MESSAGES.USER_NOT_FOUND);
        logger.info(`Usuário ${id} deletado`);
        return MESSAGES.USER_DELETED;
    }

    return { remove };
}

module.exports = { createUserService };
