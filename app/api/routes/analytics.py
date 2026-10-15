from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.analytics import AnalyticsResponse
from app.core.database import get_db_session
from app.services.task_service import TaskService

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(session: AsyncSession = Depends(get_db_session)) -> AnalyticsResponse:
    return await TaskService(session).analytics()
