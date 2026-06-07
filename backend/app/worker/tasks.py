"""
Celery task definitions for experiment execution.
"""

from __future__ import annotations

import logging

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.worker.tasks.run_experiment_task",
    bind=True,
    max_retries=0,
    acks_late=True,
    track_started=True,
    queue="experiments",
)
def run_experiment_task(self, experiment_id: str) -> dict:
    """
    Celery task entry point for running an experiment.

    Calls the engine runner which orchestrates the full pipeline:
    load context → plan → generate → execute → judge → score → finalize.
    """
    logger.info("Starting experiment task: %s (celery_id=%s)", experiment_id, self.request.id)

    try:
        from app.engine.runner import run_experiment

        run_experiment(experiment_id)
        logger.info("Experiment %s completed", experiment_id)
        return {"experiment_id": experiment_id, "status": "completed"}

    except Exception as exc:
        logger.exception("Experiment %s failed with unhandled error", experiment_id)
        # Update experiment status to failed
        try:
            import asyncio
            from sqlalchemy import update
            from app.storage.database import AsyncSessionLocal
            from app.storage.models.experiment import Experiment

            async def _mark_failed():
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(Experiment)
                        .where(Experiment.id == experiment_id)
                        .values(
                            status="failed",
                            error_message=str(exc)[:2000],
                            status_message=f"failed: {str(exc)[:200]}",
                        )
                    )
                    await session.commit()

            asyncio.run(_mark_failed())
        except Exception:
            logger.exception("Failed to mark experiment %s as failed in DB", experiment_id)

        return {
            "experiment_id": experiment_id,
            "status": "failed",
            "error": str(exc),
        }
