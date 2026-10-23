class ReportController {
    constructor(reportService) {
        this.reportService = reportService;
    }

    async financialReport(req, res) {
        res.json(await this.reportService.financialReport());
    }
}

module.exports = ReportController;
