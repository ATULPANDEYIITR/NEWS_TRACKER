from datetime import datetime, timezone

from sqlalchemy import text

from app.database.session import SessionLocal
from app.analytics.source_monitor import (
    create_monitoring_tables,
)


def update_monitoring_snapshot():

    db = SessionLocal()

    try:

        create_monitoring_tables(db)

        rows = db.execute(
            text(
                """
                SELECT
                    s.id,
                    s.feed_url
                FROM sources s
                WHERE s.is_active = TRUE
                """
            )
        ).mappings().all()

        for row in rows:

            source_id = row["id"]

            latest = db.execute(
                text(
                    """
                    SELECT
                        status,
                        response_time_ms,
                        articles_found,
                        error_message
                    FROM source_health
                    WHERE source_id = :source_id
                    ORDER BY checked_at DESC
                    LIMIT 1
                    """
                ),
                {
                    "source_id":
                        source_id
                },
            ).mappings().first()

            if latest:

                db.execute(
                    text(
                        """
                        INSERT INTO source_monitoring
                        (
                            source_id,
                            checked_at,
                            status,
                            response_time_ms,
                            articles_found,
                            error_message,
                            feed_url
                        )
                        VALUES
                        (
                            :source_id,
                            :checked_at,
                            :status,
                            :response_time_ms,
                            :articles_found,
                            :error_message,
                            :feed_url
                        )
                        """
                    ),
                    {
                        "source_id":
                            source_id,

                        "checked_at":
                            datetime.now(
                                timezone.utc
                            ),

                        "status":
                            latest["status"]
                            or "unknown",

                        "response_time_ms":
                            latest[
                                "response_time_ms"
                            ],

                        "articles_found":
                            latest[
                                "articles_found"
                            ]
                            or 0,

                        "error_message":
                            latest[
                                "error_message"
                            ],

                        "feed_url":
                            row["feed_url"],
                    },
                )

        db.commit()

        print(
            f"Source monitoring snapshot updated: "
            f"{len(rows)} sources"
        )

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


if __name__ == "__main__":
    update_monitoring_snapshot()
