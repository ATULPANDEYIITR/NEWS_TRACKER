from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database.session import SessionLocal

router = APIRouter(
    prefix="/api/monitoring",
    tags=["Source Monitoring"],
)


def determine_status(
    active,
    feed_url,
    latest_status,
    last_checked,
):

    if not active:
        return "inactive"

    if not feed_url:
        return "not_configured"

    if latest_status == "error":
        return "error"

    if latest_status == "success":

        if last_checked:

            age_seconds = (
                datetime.now(timezone.utc)
                - last_checked
            ).total_seconds()

            if age_seconds > (
                6 * 60 * 60
            ):
                return "stale"

        return "healthy"

    return "unknown"


@router.get("/sources")
def source_monitoring(
    status: str | None = None,
    limit: int = Query(
        default=200,
        ge=1,
        le=500,
    ),
):

    db = SessionLocal()

    try:

        rows = db.execute(
            text(
                """
                SELECT
                    s.id,
                    s.name,
                    s.website_url,
                    s.feed_url,
                    s.country,
                    s.region,
                    s.language,
                    s.is_active,

                    COUNT(a.id)
                        AS total_articles,

                    MAX(a.published_at)
                        AS latest_article,

                    (
                        SELECT sm.status
                        FROM source_monitoring sm
                        WHERE sm.source_id = s.id
                        ORDER BY sm.checked_at DESC
                        LIMIT 1
                    ) AS latest_status,

                    (
                        SELECT sm.checked_at
                        FROM source_monitoring sm
                        WHERE sm.source_id = s.id
                        ORDER BY sm.checked_at DESC
                        LIMIT 1
                    ) AS last_checked,

                    (
                        SELECT sm.response_time_ms
                        FROM source_monitoring sm
                        WHERE sm.source_id = s.id
                        ORDER BY sm.checked_at DESC
                        LIMIT 1
                    ) AS response_time_ms,

                    (
                        SELECT sm.articles_found
                        FROM source_monitoring sm
                        WHERE sm.source_id = s.id
                        ORDER BY sm.checked_at DESC
                        LIMIT 1
                    ) AS last_articles_found,

                    (
                        SELECT sm.error_message
                        FROM source_monitoring sm
                        WHERE sm.source_id = s.id
                        ORDER BY sm.checked_at DESC
                        LIMIT 1
                    ) AS latest_error

                FROM sources s

                LEFT JOIN articles a
                    ON a.source_id = s.id

                GROUP BY
                    s.id,
                    s.name,
                    s.website_url,
                    s.feed_url,
                    s.country,
                    s.region,
                    s.language,
                    s.is_active

                ORDER BY
                    s.name

                LIMIT :limit
                """
            ),
            {
                "limit": limit
            },
        ).mappings().all()

        result = []

        for row in rows:

            current_status = determine_status(
                row["is_active"],
                row["feed_url"],
                row["latest_status"],
                row["last_checked"],
            )

            if (
                status
                and current_status != status
            ):
                continue

            result.append(
                {
                    "source_id": row["id"],
                    "source": row["name"],
                    "website_url":
                        row["website_url"],
                    "feed_url":
                        row["feed_url"],
                    "country":
                        row["country"],
                    "region":
                        row["region"],
                    "language":
                        row["language"],
                    "active":
                        row["is_active"],
                    "status":
                        current_status,
                    "total_articles":
                        int(
                            row["total_articles"] or 0
                        ),
                    "latest_article":
                        (
                            row["latest_article"].isoformat()
                            if row["latest_article"]
                            else None
                        ),
                    "last_checked":
                        (
                            row["last_checked"].isoformat()
                            if row["last_checked"]
                            else None
                        ),
                    "response_time_ms":
                        row["response_time_ms"],
                    "last_articles_found":
                        int(
                            row["last_articles_found"] or 0
                        ),
                    "latest_error":
                        row["latest_error"],
                }
            )

        return {
            "generated_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "count":
                len(result),

            "sources":
                result,
        }

    finally:

        db.close()


@router.get("/summary")
def monitoring_summary():

    db = SessionLocal()

    try:

        rows = db.execute(
            text(
                """
                SELECT
                    s.id,
                    s.feed_url,
                    s.is_active,

                    (
                        SELECT sm.status
                        FROM source_monitoring sm
                        WHERE sm.source_id = s.id
                        ORDER BY sm.checked_at DESC
                        LIMIT 1
                    ) AS latest_status,

                    (
                        SELECT sm.checked_at
                        FROM source_monitoring sm
                        WHERE sm.source_id = s.id
                        ORDER BY sm.checked_at DESC
                        LIMIT 1
                    ) AS last_checked

                FROM sources s
                """
            )
        ).mappings().all()

        summary = {
            "total": 0,
            "healthy": 0,
            "error": 0,
            "stale": 0,
            "not_configured": 0,
            "inactive": 0,
            "unknown": 0,
        }

        for row in rows:

            current_status = determine_status(
                row["is_active"],
                row["feed_url"],
                row["latest_status"],
                row["last_checked"],
            )

            summary["total"] += 1
            summary[current_status] += 1

        return {
            "generated_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "summary":
                summary,
        }

    finally:

        db.close()


@router.get("/history/{source_id}")
def source_history(
    source_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
):

    db = SessionLocal()

    try:

        rows = db.execute(
            text(
                """
                SELECT
                    checked_at,
                    status,
                    response_time_ms,
                    articles_found,
                    error_message,
                    feed_url
                FROM source_monitoring
                WHERE source_id = :source_id
                ORDER BY checked_at DESC
                LIMIT :limit
                """
            ),
            {
                "source_id":
                    source_id,

                "limit":
                    limit,
            },
        ).mappings().all()

        return {
            "source_id":
                source_id,

            "history": [
                {
                    "checked_at":
                        row["checked_at"].isoformat(),

                    "status":
                        row["status"],

                    "response_time_ms":
                        row["response_time_ms"],

                    "articles_found":
                        row["articles_found"],

                    "error_message":
                        row["error_message"],

                    "feed_url":
                        row["feed_url"],
                }

                for row in rows
            ],
        }

    finally:

        db.close()
