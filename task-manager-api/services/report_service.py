from datetime import timedelta

from models.category import Category
from models.database import utc_now
from models.task import HIGH_PRIORITY_MAX, Task
from models.user import User

RECENT_ACTIVITY_DAYS = 7
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def _completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


def build_summary():
    status_counts = Task.count_grouped(Task.status)
    priority_counts = Task.count_grouped(Task.priority)

    now = utc_now()
    overdue_tasks = [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in Task.list_all() if task.is_overdue()
    ]

    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    totals_by_user = Task.totals_by_user()
    user_productivity = []
    for user in User.list_all():
        total, completed = totals_by_user.get(user.id, (0, 0))
        user_productivity.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': _completion_rate(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count_all(),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': {
            'pending': status_counts.get('pending', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'done': status_counts.get('done', 0),
            'cancelled': status_counts.get('cancelled', 0),
        },
        'tasks_by_priority': {
            label: priority_counts.get(priority, 0)
            for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': overdue_tasks,
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_done_updated_since(since),
        },
        'user_productivity': user_productivity,
    }


def build_user_report(user):
    tasks = Task.list_for_user(user.id)
    total = len(tasks)
    done = sum(1 for task in tasks if task.status == 'done')
    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': sum(1 for task in tasks if task.status == 'pending'),
            'in_progress': sum(1 for task in tasks if task.status == 'in_progress'),
            'cancelled': sum(1 for task in tasks if task.status == 'cancelled'),
            'overdue': sum(1 for task in tasks if task.is_overdue()),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': _completion_rate(done, total),
        },
    }


def build_task_stats():
    status_counts = Task.count_grouped(Task.status)
    total = Task.count_all()
    done = status_counts.get('done', 0)
    return {
        'total': total,
        'pending': status_counts.get('pending', 0),
        'in_progress': status_counts.get('in_progress', 0),
        'done': done,
        'cancelled': status_counts.get('cancelled', 0),
        'overdue': sum(1 for task in Task.list_all() if task.is_overdue()),
        'completion_rate': _completion_rate(done, total),
    }
