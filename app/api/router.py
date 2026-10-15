from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.tasks import router as tasks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(tasks_router)
api_router.include_router(analytics_router)
