from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.api.routes.news import router as news_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.live import router as live_router
from app.api.routes.intelligence import router as intelligence_router
from app.core.config import settings
from app.core.logging import setup_logging


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Global News Tracker and News Intelligence Platform",
    version="0.3.0",
    lifespan=lifespan,
)


app.include_router(health_router)
app.include_router(news_router)
app.include_router(dashboard_router)
app.include_router(live_router)
app.include_router(intelligence_router)


app.mount(
    "/frontend",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="frontend",
)


@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )



@app.get("/source-health", include_in_schema=False)
def source_health_page():
    return FileResponse(
        FRONTEND_DIR / "source-health.html"
    )
@app.get("/")
def root() -> dict:
    return {
        "application": settings.app_name,
        "status": "running",
        "version": "0.3.0",
        "message": "Global News Tracker API is running.",
        "dashboard": "/dashboard",
        "docs": "/docs",
    }







