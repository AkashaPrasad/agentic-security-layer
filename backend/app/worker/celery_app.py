"""
Celery worker application and configuration.
"""

from celery import Celery

from app.config import settings

# Use Redis DB0 for Celery broker/backend (per design)
_broker = settings.celery_broker_url or settings.redis_connection_url
_backend = settings.celery_result_backend or settings.redis_connection_url

celery_app = Celery(
    "ai_red_team",
    broker=_broker,
    backend=_backend,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Concurrency
    worker_concurrency=settings.celery_worker_concurrency,
    # Task behaviour
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Result expiry (24 hours)
    result_expires=86400,
    # Task routes
    task_routes={
        "app.worker.tasks.run_experiment_task": {"queue": "experiments"},
    },
    # Retry policy for broker connection
    broker_connection_retry_on_startup=True,
)

# Auto-discover tasks module
celery_app.autodiscover_tasks(["app.worker"])
