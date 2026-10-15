import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.task import TaskCreateRequest, TaskCreateResponse, TaskResponse
from app.core.database import get_db_session
from app.services.task_service import TaskService
from app.tasks.worker import process_task_job

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    payload: TaskCreateRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TaskCreateResponse:
    service = TaskService(session)
    task = await service.create_task([str(url) for url in payload.source_urls])

    celery_result = process_task_job.delay(str(task.id))
    await service.save_celery_task_id(task, celery_result.id)

    response.headers["Location"] = f"/api/v1/tasks/{task.id}"
    return TaskCreateResponse(task_id=task.id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    return await TaskService(session).get_task(task_id)
