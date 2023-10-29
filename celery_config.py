from celery import Celery
from celery.schedules import crontab

celery = Celery(
    'app',
    broker='redis://localhost:6379/0',
    include=['app.tasks']
)

schedule = crontab(hour=20, minute=0, day_of_week=1)

celery.conf.beat_schedule = {
    'save-discover-weekly': {
        'task': 'app.tasks.save_discover_weekly_task',
        'schedule': schedule,
    },
}
