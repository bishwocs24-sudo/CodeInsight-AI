import logging
import sys
import time

from celery import Celery

from app.core.config import get_settings
from app.platform_review.jobs import cleanup, execute, ready_jobs

celery = Celery("codeguard", broker=get_settings().redis_url)
celery.conf.update(
    accept_content=["json"], task_ignore_result=True, worker_prefetch_multiplier=1,
    task_acks_late=True, task_reject_on_worker_lost=True,
    task_time_limit=235, broker_connection_retry_on_startup=True,
    beat_schedule={
        "dispatch-reviews": {"task": "codeguard.dispatch", "schedule": 5.0},
        "expire-reviews": {"task": "codeguard.cleanup", "schedule": 3600.0},
    },
)
run = celery.task(name="codeguard.execute")(execute)
celery.task(name="codeguard.cleanup")(cleanup)


@celery.task(name="codeguard.dispatch")
def dispatch():
    for job_id in ready_jobs():
        run.apply_async(args=[job_id], expires=20)


if __name__ == "__main__":
    if sys.argv[1:] != ["local"] or get_settings().production:
        sys.exit("Use Celery worker and beat in production. Local command: python -m app.platform_review.worker local")
    logging.basicConfig(level=logging.INFO)
    last_cleanup = 0.0
    while True:
        if time.monotonic() - last_cleanup > 3600 or not last_cleanup:
            cleanup()
            last_cleanup = time.monotonic()
        for job_id in ready_jobs():
            execute(job_id)
        time.sleep(2)
