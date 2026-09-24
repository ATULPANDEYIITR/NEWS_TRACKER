from fastapi import APIRouter

from app.api.routes.news import router as news_router
from app.api.routes.dashboard import router as dashboard_router

router = APIRouter()

router.include_router(news_router)
router.include_router(dashboard_router)
