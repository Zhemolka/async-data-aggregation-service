import asyncio
import random
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionFactory
from app.models.task import AggregationTask, TaskStatus
from app.services.url_simulator import simulate_url_request
from app.tasks.celery_app import celery_app


async def mark_failed(session: AsyncSession, task: AggregationTask, message: str) -> None:
    task.status = TaskStatus.failed
    task.error_message = message
    await session.commit()


async def process_task(task_id: uuid.UUID) -> None:
    async with AsyncSessionFactory() as session:
        task = await session.get(AggregationTask, task_id)
        if task is None:
            raise LookupError(f"Task {task_id} does not exist")

        task.status = TaskStatus.processing
        task.error_message = None
        await session.commit()

        try:
            for url in task.source_urls:
                await simulate_url_request(url)
                task.urls_processed += 1
                await session.commit()

            task.status = TaskStatus.completed
            task.metrics_generated = random.randint(10, 100)
            await session.commit()
        except Exception as exc:
            await mark_failed(session, task, str(exc))
            raise


@celery_app.task(name="aggregation.process_task")
def process_task_job(task_id: str) -> None:
    asyncio.run(process_task(uuid.UUID(task_id)))
