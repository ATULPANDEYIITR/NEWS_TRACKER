from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database.session import SessionLocal


router = APIRouter(
    prefix="/api/intelligence",
    tags=["Article Intelligence"],
)


@router.get("/articles")
def intelligence_articles(
    topic: str | None = None,
    entity: str | None = None,
    country: str | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
):

    db = SessionLocal()

    try:

        conditions = []
        params = {
            "limit": limit,
        }

        if topic:

            conditions.append(
                """
                LOWER(ai.topics)
                LIKE LOWER(:topic)
                """
            )

            params["topic"] = f"%{topic}%"

        if entity:

            conditions.append(
                """
                LOWER(ai.entities)
                LIKE LOWER(:entity)
                """
            )

            params["entity"] = f"%{entity}%"

        if country:

            conditions.append(
                """
                LOWER(ai.geographic_signals)
                LIKE LOWER(:country)
                """
            )

            params["country"] = f"%{country}%"

        where_clause = ""

        if conditions:

            where_clause = (
                "WHERE "
                + " AND ".join(
                    conditions
                )
            )

        rows = db.execute(
            text(
                f"""
                SELECT
                    a.id,
                    a.headline,
                    a.canonical_url,
                    a.published_at,
                    s.name AS source_name,

                    ai.primary_topic,
                    ai.topics,
                    ai.entities,
                    ai.geographic_signals,

                    ai.political_signal,
                    ai.economic_signal,
                    ai.technology_signal,
                    ai.conflict_signal,
                    ai.health_signal,
                    ai.climate_signal,
                    ai.breaking_signal,

                    ai.keyword_count,
                    ai.analyzed_at

                FROM article_intelligence ai

                JOIN articles a
                    ON a.id = ai.article_id

                JOIN sources s
                    ON s.id = a.source_id

                {where_clause}

                ORDER BY
                    a.published_at DESC NULLS LAST

                LIMIT :limit
                """
            ),
            params,
        ).mappings().all()

        return {
            "generated_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "count":
                len(rows),

            "articles": [
                {
                    "id":
                        row["id"],

                    "headline":
                        row["headline"],

                    "source":
                        row["source_name"],

                    "published_at":
                        (
                            row["published_at"].isoformat()
                            if row["published_at"]
                            else None
                        ),

                    "original_url":
                        row["canonical_url"],

                    "primary_topic":
                        row["primary_topic"],

                    "topics":
                        [
                            item.strip()
                            for item in
                            (
                                row["topics"]
                                or ""
                            ).split(",")
                            if item.strip()
                        ],

                    "entities":
                        [
                            item.strip()
                            for item in
                            (
                                row["entities"]
                                or ""
                            ).split(",")
                            if item.strip()
                        ],

                    "geographic_signals":
                        [
                            item.strip()
                            for item in
                            (
                                row[
                                    "geographic_signals"
                                ]
                                or ""
                            ).split(",")
                            if item.strip()
                        ],

                    "signals": {
                        "political":
                            bool(
                                row[
                                    "political_signal"
                                ]
                            ),

                        "economic":
                            bool(
                                row[
                                    "economic_signal"
                                ]
                            ),

                        "technology":
                            bool(
                                row[
                                    "technology_signal"
                                ]
                            ),

                        "conflict":
                            bool(
                                row[
                                    "conflict_signal"
                                ]
                            ),

                        "health":
                            bool(
                                row[
                                    "health_signal"
                                ]
                            ),

                        "climate":
                            bool(
                                row[
                                    "climate_signal"
                                ]
                            ),

                        "breaking":
                            bool(
                                row[
                                    "breaking_signal"
                                ]
                            ),
                    },

                    "keyword_count":
                        row[
                            "keyword_count"
                        ],

                    "analyzed_at":
                        row[
                            "analyzed_at"
                        ].isoformat(),
                }

                for row in rows
            ],
        }

    finally:

        db.close()


@router.get("/article/{article_id}")
def intelligence_article(
    article_id: int,
):

    db = SessionLocal()

    try:

        row = db.execute(
            text(
                """
                SELECT
                    a.id,
                    a.headline,
                    a.canonical_url,
                    a.published_at,
                    s.name AS source_name,

                    ai.primary_topic,
                    ai.topics,
                    ai.entities,
                    ai.geographic_signals,

                    ai.political_signal,
                    ai.economic_signal,
                    ai.technology_signal,
                    ai.conflict_signal,
                    ai.health_signal,
                    ai.climate_signal,
                    ai.breaking_signal,

                    ai.keyword_count,
                    ai.analyzed_at

                FROM article_intelligence ai

                JOIN articles a
                    ON a.id = ai.article_id

                JOIN sources s
                    ON s.id = a.source_id

                WHERE a.id = :article_id
                """
            ),
            {
                "article_id":
                    article_id
            },
        ).mappings().first()

        if not row:

            return {
                "found": False,
                "article_id":
                    article_id,
            }

        return {
            "found": True,

            "article": {
                "id":
                    row["id"],

                "headline":
                    row["headline"],

                "source":
                    row["source_name"],

                "published_at":
                    (
                        row["published_at"].isoformat()
                        if row["published_at"]
                        else None
                    ),

                "original_url":
                    row["canonical_url"],

                "primary_topic":
                    row["primary_topic"],

                "topics":
                    [
                        item.strip()
                        for item in
                        (
                            row["topics"]
                            or ""
                        ).split(",")
                        if item.strip()
                    ],

                "entities":
                    [
                        item.strip()
                        for item in
                        (
                            row["entities"]
                            or ""
                        ).split(",")
                        if item.strip()
                    ],

                "geographic_signals":
                    [
                        item.strip()
                        for item in
                        (
                            row[
                                "geographic_signals"
                            ]
                            or ""
                        ).split(",")
                        if item.strip()
                    ],

                "signals": {
                    "political":
                        bool(
                            row[
                                "political_signal"
                            ]
                        ),

                    "economic":
                        bool(
                            row[
                                "economic_signal"
                            ]
                        ),

                    "technology":
                        bool(
                            row[
                                "technology_signal"
                            ]
                        ),

                    "conflict":
                        bool(
                            row[
                                "conflict_signal"
                            ]
                        ),

                    "health":
                        bool(
                            row[
                                "health_signal"
                            ]
                        ),

                    "climate":
                        bool(
                            row[
                                "climate_signal"
                            ]
                        ),

                    "breaking":
                        bool(
                            row[
                                "breaking_signal"
                            ]
                        ),
                },

                "keyword_count":
                    row[
                        "keyword_count"
                    ],

                "analyzed_at":
                    row[
                        "analyzed_at"
                    ].isoformat(),
            },
        }

    finally:

        db.close()
