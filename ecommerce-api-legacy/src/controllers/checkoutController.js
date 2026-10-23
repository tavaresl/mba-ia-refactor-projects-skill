class CheckoutController {
    constructor(checkoutService) {
        this.checkoutService = checkoutService;
    }

    async checkout(req, res) {
        const { enrollmentId } = await this.checkoutService.checkout(req.checkoutInput);
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    }
}

module.exports = CheckoutController;
