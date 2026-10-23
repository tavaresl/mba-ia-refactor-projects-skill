from middlewares.errors import ApiError
from models.user import User
from services import report_service


def summary():
    return report_service.build_summary()


def user_report(user_id):
    user = User.find_by_id(user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)
    return report_service.build_user_report(user)


def task_stats():
    return report_service.build_task_stats()
