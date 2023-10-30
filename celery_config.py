from celery import Celery
from celery.schedules import crontab
import redis

redis_pool = redis.ConnectionPool.from_url(
    'rediss://red-ckvgp5eb0mos739hsp7g:mEzjJ1KfNYnB9V0hm5RPpeZ0DrS01wW3@oregon-redis.render.com:6379?ssl_cert_reqs=CERT_NONE'
)

celery = Celery(
    'app',
    broker='rediss://red-ckvgp5eb0mos739hsp7g:mEzjJ1KfNYnB9V0hm5RPpeZ0DrS01wW3@oregon-redis.render.com:6379?ssl_cert_reqs=CERT_NONE',
    include=['tasks']
)

schedule = crontab(hour=5, minute=54, day_of_week=1)

celery.conf.beat_schedule = {
    'save-discover-weekly': {
        'task': 'tasks.save_discover_weekly_task',
        'schedule': schedule,
    },
}
