"""Estatísticas e relatórios (agregações no banco, sem N+1)."""
from datetime import timedelta

from sqlalchemy import case, func, select

from config.constants import (
    HIGH_PRIORITY_MAX,
    PRIORITY_LABELS,
    RECENT_DAYS,
    TASK_STATUS_CANCELLED,
    TASK_STATUS_DONE,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_PENDING,
)
from middlewares.errors import ApiError
from models import Category, Task, User, db
from utils.dates import utc_now


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


def _count(*conditions):
    statement = select(func.count()).select_from(Task)
    for condition in conditions:
        statement = statement.where(condition)
    return db.session.scalar(statement)


def _counts_by(column, *conditions):
    statement = select(column, func.count()).group_by(column)
    for condition in conditions:
        statement = statement.where(condition)
    return {key: count for key, count in db.session.execute(statement).all()}


def task_stats():
    by_status = _counts_by(Task.status)
    total = _count()
    done = by_status.get(TASK_STATUS_DONE, 0)
    return {
        'total': total,
        'pending': by_status.get(TASK_STATUS_PENDING, 0),
        'in_progress': by_status.get(TASK_STATUS_IN_PROGRESS, 0),
        'done': done,
        'cancelled': by_status.get(TASK_STATUS_CANCELLED, 0),
        'overdue': _count(Task.overdue_filter(utc_now())),
        'completion_rate': completion_rate(done, total),
    }


def summary_report():
    now = utc_now()
    by_status = _counts_by(Task.status)
    by_priority = _counts_by(Task.priority)

    overdue_tasks = db.session.execute(
        select(Task).where(Task.overdue_filter(now)).order_by(Task.id)
    ).scalars().all()
    overdue_list = [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in overdue_tasks
    ]

    window_start = now - timedelta(days=RECENT_DAYS)
    recent_created = _count(Task.created_at >= window_start)
    recent_done = _count(Task.status == TASK_STATUS_DONE, Task.updated_at >= window_start)

    per_user = {
        user_id: (total, completed or 0)
        for user_id, total, completed in db.session.execute(
            select(
                Task.user_id,
                func.count(),
                func.sum(case((Task.status == TASK_STATUS_DONE, 1), else_=0)),
            )
            .where(Task.user_id.isnot(None))
            .group_by(Task.user_id)
        ).all()
    }
    users = db.session.execute(select(User).order_by(User.id)).scalars().all()
    user_stats = []
    for user in users:
        total, completed = per_user.get(user.id, (0, 0))
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': completion_rate(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': _count(),
            'total_users': db.session.scalar(select(func.count()).select_from(User)),
            'total_categories': db.session.scalar(select(func.count()).select_from(Category)),
        },
        'tasks_by_status': {
            'pending': by_status.get(TASK_STATUS_PENDING, 0),
            'in_progress': by_status.get(TASK_STATUS_IN_PROGRESS, 0),
            'done': by_status.get(TASK_STATUS_DONE, 0),
            'cancelled': by_status.get(TASK_STATUS_CANCELLED, 0),
        },
        'tasks_by_priority': {
            label: by_priority.get(priority, 0)
            for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_created,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)

    of_user = Task.user_id == user_id
    by_status = _counts_by(Task.status, of_user)
    total = _count(of_user)
    done = by_status.get(TASK_STATUS_DONE, 0)

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': by_status.get(TASK_STATUS_PENDING, 0),
            'in_progress': by_status.get(TASK_STATUS_IN_PROGRESS, 0),
            'cancelled': by_status.get(TASK_STATUS_CANCELLED, 0),
            'overdue': _count(of_user, Task.overdue_filter(utc_now())),
            'high_priority': _count(of_user, Task.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': completion_rate(done, total),
        },
    }
