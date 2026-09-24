from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database.session import SessionLocal

router = APIRouter(
    prefix="/api/monitoring",
    tags=["Collection Reliability"],
)


@router.get("/collection")
def collection_reliability(
    hours: int = Query(
        default=24,
        ge=1,
        le=720,
    )
):

    db = SessionLocal()

    try:

        since = (
            datetime.now(timezone.utc)
            - timedelta(hours=hours)
        )

        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    started_at,
                    finished_at,
                    attempt,
                    status,
                    exit_code,
                    duration_seconds,
                    message
                FROM collection_reliability_log
                WHERE started_at >= :since
                ORDER BY started_at DESC, attempt DESC
                LIMIT 500
                """
            ),
            {"since": since},
        ).mappings().all()

        summary_rows = db.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_attempts,

                    COUNT(*) FILTER (
                        WHERE status = 'success'
                    ) AS successful_attempts,

                    COUNT(*) FILTER (
                        WHERE status = 'failed'
                    ) AS failed_runs,

                    COUNT(*) FILTER (
                        WHERE status = 'skipped_locked'
                    ) AS skipped_runs

                FROM collection_reliability_log
                WHERE started_at >= :since
                """
            ),
            {"since": since},
        ).mappings().first()

        return {
            "hours": hours,
            "generated_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "summary": {
                "total_attempts":
                    int(
                        summary_rows[
                            "total_attempts"
                        ] or 0
                    ),

                "successful_attempts":
                    int(
                        summary_rows[
                            "successful_attempts"
                        ] or 0
                    ),

                "failed_runs":
                    int(
                        summary_rows[
                            "failed_runs"
                        ] or 0
                    ),

                "skipped_runs":
                    int(
                        summary_rows[
                            "skipped_runs"
                        ] or 0
                    ),
            },

            "runs": [
                {
                    "id":
                        row["id"],

                    "started_at":
                        row["started_at"].isoformat(),

                    "finished_at":
                        (
                            row["finished_at"].isoformat()
                            if row["finished_at"]
                            else None
                        ),

                    "attempt":
                        row["attempt"],

                    "status":
                        row["status"],

                    "exit_code":
                        row["exit_code"],

                    "duration_seconds":
                        row["duration_seconds"],

                    "message":
                        row["message"],
                }

                for row in rows
            ],
        }

    finally:

        db.close()
