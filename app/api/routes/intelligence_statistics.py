from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.database.session import SessionLocal


router = APIRouter(
    prefix="/api/intelligence",
    tags=["Intelligence Statistics"],
)


@router.get("/statistics")
def intelligence_statistics():

    db = SessionLocal()

    try:

        total_articles = db.execute(
            text(
                "SELECT COUNT(*) FROM articles"
            )
        ).scalar() or 0

        analyzed_articles = db.execute(
            text(
                "SELECT COUNT(*) "
                "FROM article_intelligence"
            )
        ).scalar() or 0

        topics = db.execute(
            text(
                """
                SELECT
                    primary_topic,
                    COUNT(*) AS article_count
                FROM article_intelligence
                GROUP BY primary_topic
                ORDER BY article_count DESC
                LIMIT 30
                """
            )
        ).mappings().all()

        signals = db.execute(
            text(
                """
                SELECT

                    COUNT(*) FILTER (
                        WHERE political_signal = TRUE
                    ) AS political,

                    COUNT(*) FILTER (
                        WHERE economic_signal = TRUE
                    ) AS economic,

                    COUNT(*) FILTER (
                        WHERE technology_signal = TRUE
                    ) AS technology,

                    COUNT(*) FILTER (
                        WHERE conflict_signal = TRUE
                    ) AS conflict,

                    COUNT(*) FILTER (
                        WHERE health_signal = TRUE
                    ) AS health,

                    COUNT(*) FILTER (
                        WHERE climate_signal = TRUE
                    ) AS climate,

                    COUNT(*) FILTER (
                        WHERE breaking_signal = TRUE
                    ) AS breaking

                FROM article_intelligence
                """
            )
        ).mappings().first()

        geographic = db.execute(
            text(
                """
                SELECT
                    geographic_signals,
                    COUNT(*) AS article_count
                FROM article_intelligence
                WHERE
                    geographic_signals IS NOT NULL
                    AND TRIM(geographic_signals) <> ''
                GROUP BY geographic_signals
                ORDER BY article_count DESC
                LIMIT 30
                """
            )
        ).mappings().all()

        return {
            "generated_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "coverage": {
                "total_articles":
                    int(total_articles),

                "analyzed_articles":
                    int(analyzed_articles),

                "remaining_articles":
                    max(
                        0,
                        int(total_articles)
                        - int(analyzed_articles),
                    ),

                "coverage_percent":
                    round(
                        (
                            analyzed_articles
                            / total_articles
                            * 100
                        )
                        if total_articles
                        else 0,
                        2,
                    ),
            },

            "topics": [
                {
                    "topic":
                        row["primary_topic"],

                    "article_count":
                        int(
                            row["article_count"]
                        ),
                }

                for row in topics
            ],

            "signals": {
                "political":
                    int(
                        signals["political"]
                        or 0
                    ),

                "economic":
                    int(
                        signals["economic"]
                        or 0
                    ),

                "technology":
                    int(
                        signals["technology"]
                        or 0
                    ),

                "conflict":
                    int(
                        signals["conflict"]
                        or 0
                    ),

                "health":
                    int(
                        signals["health"]
                        or 0
                    ),

                "climate":
                    int(
                        signals["climate"]
                        or 0
                    ),

                "breaking":
                    int(
                        signals["breaking"]
                        or 0
                    ),
            },

            "geographic_signals": [
                {
                    "locations":
                        row[
                            "geographic_signals"
                        ],

                    "article_count":
                        int(
                            row[
                                "article_count"
                            ]
                        ),
                }

                for row in geographic
            ],
        }

    finally:

        db.close()
