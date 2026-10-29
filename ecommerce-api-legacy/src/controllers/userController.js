function createUserController({ userService }) {
    return {
        async remove(req, res) {
            res.send(await userService.remove(req.input.id));
        },
    };
}

module.exports = { createUserController };
