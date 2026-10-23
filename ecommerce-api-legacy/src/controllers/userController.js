class UserController {
    constructor(userService) {
        this.userService = userService;
    }

    async deleteUser(req, res) {
        await this.userService.deleteUser(req.userId);
        res.send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
    }
}

module.exports = UserController;
