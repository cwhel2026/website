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
        "bookkeeping-categorize": {
            "task": "rmd.bookkeeping_categorize",
            "schedule": crontab(minute=40, hour="*/4"),
        },
        "financial-watchdog-daily": {
            "task": "rmd.financial_watchdog",
            "schedule": crontab(minute=0, hour=7),
        },
        "finance-report-daily": {
            "task": "rmd.finance_report_daily",
            "schedule": crontab(minute=45, hour=6),
        },
        "finance-report-weekly": {
            "task": "rmd.finance_report_weekly",
            "schedule": crontab(minute=0, hour=8, day_of_week="sun"),
        },
        "finance-report-monthly": {
            "task": "rmd.finance_report_monthly",
            "schedule": crontab(minute=0, hour=9, day_of_month=1),
        },
        "finance-report-annual-check": {
            "task": "rmd.finance_report_annual",
            "schedule": crontab(minute=15, hour=7),
        },
        "finance-task-centre-weekly": {
            "task": "rmd.finance_task_centre_notify",
            "schedule": crontab(minute=15, hour=8, day_of_week="mon"),
        },
    },
    timezone="Europe/London",
)