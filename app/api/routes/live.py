from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/live", tags=["Live News"])

ROOT = Path(__file__).resolve().parents[3]
LOG_FILE = ROOT / "logs" / "live_news_update.log"


@router.get("/status")
def live_status():
    last_modified = None

    if LOG_FILE.exists():
        timestamp = datetime.fromtimestamp(
            LOG_FILE.stat().st_mtime,
            tz=timezone.utc,
        )
        last_modified = timestamp.isoformat()

    return {
        "live_collection_enabled": True,
        "schedule": "Every 30 minutes",
        "dashboard_refresh": "Every 60 seconds",
        "last_collection_log_update": last_modified,
        "log_file": "logs/live_news_update.log",
    }
