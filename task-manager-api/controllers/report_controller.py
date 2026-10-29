from services import report_service


def summary_report():
    return report_service.summary_report()


def user_report(user_id):
    return report_service.user_report(user_id)
