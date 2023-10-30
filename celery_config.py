from celery import Celery
from celery.schedules import crontab

celery = Celery(
    'app',
    broker='redis://red-ckvgp5eb0mos739hsp7g:6379',
    include=['app.tasks']
)

schedule = crontab(hour=21, minute=45, day_of_week=0)

celery.conf.beat_schedule = {
    'save-discover-weekly': {
        'task': 'app.tasks.save_discover_weekly_task',
        'schedule': schedule,
    },
}
