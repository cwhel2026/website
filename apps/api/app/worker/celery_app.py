from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()
broker = settings.celery_broker_url or settings.redis_url

celery_app = Celery(
    "revive_my_drive",
    broker=broker,
    backend=broker,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=360,
    beat_schedule={
        "refresh-weather-hq": {
            "task": "rmd.refresh_weather_hq",
            "schedule": crontab(minute=0, hour="*/3"),
        },
        "appointment-weather-risk": {
            "task": "rmd.appointment_weather_risk",
            "schedule": crontab(minute=15, hour="*/1"),
        },
        "morning-briefing": {
            "task": "rmd.morning_briefing",
            "schedule": crontab(minute=30, hour=6),
        },
        "deliver-notifications": {
            "task": "rmd.deliver_notification_outbox",
            "schedule": crontab(minute="*/2"),
        },
        "freeagent-sync-daily": {
            "task": "rmd.freeagent_sync_incremental",
            "schedule": crontab(minute=20, hour=5),
        },
    },
    timezone="Europe/London",
)