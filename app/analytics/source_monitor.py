from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.database.session import SessionLocal


STALE_HOURS = 6


def create_monitoring_tables(db):

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS source_monitoring (
                id BIGSERIAL PRIMARY KEY,
                source_id INTEGER NOT NULL,
                checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                status VARCHAR(30) NOT NULL,
                response_time_ms DOUBLE PRECISION,
                articles_found INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                feed_url VARCHAR(2000),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )

    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS
            ix_source_monitoring_source
            ON source_monitoring(source_id)
            """
        )
    )

    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS
            ix_source_monitoring_checked
            ON source_monitoring(checked_at)
            """
        )
    )


def collect_source_status(db):

    rows = db.execute(
        text(
            """
            SELECT
                s.id,
                s.name,
                s.feed_url,
                s.is_active,

                COUNT(a.id) AS total_articles,

                MAX(a.published_at)
                    AS latest_article,

                MAX(sm.checked_at)
                    AS last_checked,

                (
                    SELECT sm2.status
                    FROM source_monitoring sm2
                    WHERE sm2.source_id = s.id
                    ORDER BY sm2.checked_at DESC
                    LIMIT 1
                ) AS latest_status,

                (
                    SELECT sm3.error_message
                    FROM source_monitoring sm3
                    WHERE sm3.source_id = s.id
                    ORDER BY sm3.checked_at DESC
                    LIMIT 1
                ) AS latest_error

            FROM sources s

            LEFT JOIN articles a
                ON a.source_id = s.id

            LEFT JOIN source_monitoring sm
                ON sm.source_id = s.id

            GROUP BY
                s.id,
                s.name,
                s.feed_url,
                s.is_active

            ORDER BY
                s.name
            """
        )
    ).mappings().all()

    return rows


def calculate_health_status(row):

    if not row["is_active"]:
        return "inactive"

    if not row["feed_url"]:
        return "not_configured"

    latest_status = row["latest_status"]

    if latest_status == "error":
        return "error"

    if latest_status == "success":

        last_checked = row["last_checked"]

        if last_checked:

            age = (
                datetime.now(timezone.utc)
                - last_checked
            )

            if age > timedelta(
                hours=STALE_HOURS
            ):
                return "stale"

        return "healthy"

    return "unknown"


def build_report():

    db = SessionLocal()

    try:

        create_monitoring_tables(db)
        db.commit()

        rows = collect_source_status(db)

        report = []

        for row in rows:

            status = calculate_health_status(
                row
            )

            report.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "feed_url": row["feed_url"],
                    "active": row["is_active"],
                    "status": status,
                    "total_articles": int(
                        row["total_articles"] or 0
                    ),
                    "latest_article": (
                        row["latest_article"]
                        .isoformat()
                        if row["latest_article"]
                        else None
                    ),
                    "last_checked": (
                        row["last_checked"]
                        .isoformat()
                        if row["last_checked"]
                        else None
                    ),
                    "latest_error":
                        row["latest_error"],
                }
            )

        return report

    finally:

        db.close()


def print_report(report):

    counts = {
        "healthy": 0,
        "error": 0,
        "stale": 0,
        "not_configured": 0,
        "inactive": 0,
        "unknown": 0,
    }

    for item in report:
        counts[item["status"]] += 1

    print()
    print(
        "SOURCE RELIABILITY SUMMARY"
    )
    print(
        "==========================="
    )

    for status, count in counts.items():
        print(
            f"{status:18}: {count}"
        )

    print()
    print(
        f"TOTAL SOURCES      : {len(report)}"
    )

    print()
    print(
        "SOURCE STATUS"
    )
    print(
        "-------------"
    )

    for item in report:

        print(
            f"{item['status']:16} | "
            f"{item['name'][:45]:45} | "
            f"articles={item['total_articles']}"
        )


if __name__ == "__main__":

    report = build_report()

    print_report(report)

    print()
    print(
        "SOURCE MONITORING: COMPLETE"
    )
