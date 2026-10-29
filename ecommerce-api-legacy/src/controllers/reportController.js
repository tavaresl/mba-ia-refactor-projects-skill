function createReportController({ financialReportService }) {
    return {
        async financial(req, res) {
            res.json(await financialReportService.build());
        },
    };
}

module.exports = { createReportController };
