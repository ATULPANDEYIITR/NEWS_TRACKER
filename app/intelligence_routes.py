from __future__ import annotations

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.intelligence import (
    build_event_clusters,
    get_intelligence_summary,
    get_multi_source_events,
)

