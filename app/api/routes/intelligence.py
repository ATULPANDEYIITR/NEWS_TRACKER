from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database.session import SessionLocal

router = APIRouter(
    prefix="/api/intelligence",
    tags=["Intelligence"],
)


@router.get("/trends")
def intelligence_trends(
    hours: int = Query(default=24, ge=1, le=720)
):
    db = SessionLocal()

    try:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        rows = db.execute(
            text("""
                SELECT
                    t.name,
                    COUNT(*) AS article_count
                FROM article_topics at
                JOIN topics t ON t.id = at.topic_id
                JOIN articles a ON a.id = at.article_id
                WHERE a.published_at >= :since
                GROUP BY t.name
                ORDER BY article_count DESC, t.name
                LIMIT 30
            """),
            {"since": since},
        ).mappings().all()

        return {
            "hours": hours,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "trends": [
                {
                    "topic": row["name"],
                    "article_count": int(row["article_count"]),
                }
                for row in rows
            ],
        }

    finally:
        db.close()


@router.get("/daily-metrics")
def daily_metrics(
    days: int = Query(default=30, ge=1, le=365)
):
    db = SessionLocal()

    try:
        since = (
            datetime.now(timezone.utc).date()
            - timedelta(days=days - 1)
        )

        rows = db.execute(
            text("""
                SELECT
                    metric_date,
                    articles_published,
                    active_sources,
                    articles_last_24_hours
                FROM daily_metrics
                WHERE metric_date >= :since
                ORDER BY metric_date
            """),
            {"since": since},
        ).mappings().all()

        return {
            "days": days,
            "metrics": [
                {
                    "date": row["metric_date"].isoformat(),
                    "articles_published": int(
                        row["articles_published"] or 0
                    ),
                    "active_sources": int(
                        row["active_sources"] or 0
                    ),
                    "articles_last_24_hours": int(
                        row["articles_last_24_hours"] or 0
                    ),
                }
                for row in rows
            ],
        }

    finally:
        db.close()


@router.get("/related/{article_id}")
def related_articles(
    article_id: int,
    limit: int = Query(default=10, ge=1, le=50),
):
    db = SessionLocal()

    try:
        rows = db.execute(
            text("""
                SELECT
                    ar.related_article_id,
                    ar.relationship_type,
                    ar.similarity_score,
                    a.headline,
                    a.canonical_url,
                    a.published_at,
                    s.name AS source_name
                FROM article_relationships ar
                JOIN articles a
                    ON a.id = ar.related_article_id
                JOIN sources s
                    ON s.id = a.source_id
                WHERE ar.article_id = :article_id
                ORDER BY
                    ar.similarity_score DESC,
                    a.published_at DESC
                LIMIT :limit
            """),
            {
                "article_id": article_id,
                "limit": limit,
            },
        ).mappings().all()

        return {
            "article_id": article_id,
            "related_articles": [
                {
                    "article_id": row["related_article_id"],
                    "relationship_type": row["relationship_type"],
                    "similarity_score": row["similarity_score"],
                    "headline": row["headline"],
                    "canonical_url": row["canonical_url"],
                    "published_at": (
                        row["published_at"].isoformat()
                        if row["published_at"]
                        else None
                    ),
                    "source": row["source_name"],
                }
                for row in rows
            ],
        }

    finally:
        db.close()


@router.get("/summary")
def intelligence_summary():
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=24)

        total_articles = db.execute(
            text("SELECT COUNT(*) FROM articles")
        ).scalar() or 0

        recent_articles = db.execute(
            text("""
                SELECT COUNT(*)
                FROM articles
                WHERE published_at >= :since
            """),
            {"since": since},
        ).scalar() or 0

        active_sources = db.execute(
            text("""
                SELECT COUNT(*)
                FROM sources
                WHERE is_active = TRUE
            """)
        ).scalar() or 0

        categories = db.execute(
            text("SELECT COUNT(*) FROM categories")
        ).scalar() or 0

        topics = db.execute(
            text("SELECT COUNT(*) FROM topics")
        ).scalar() or 0

        entities = db.execute(
            text("SELECT COUNT(*) FROM entities")
        ).scalar() or 0

        trend_rows = db.execute(
            text("""
                SELECT
                    t.name,
                    COUNT(*) AS article_count
                FROM article_topics at
                JOIN topics t ON t.id = at.topic_id
                JOIN articles a ON a.id = at.article_id
                WHERE a.published_at >= :since
                GROUP BY t.name
                ORDER BY article_count DESC, t.name
                LIMIT 10
            """),
            {"since": since},
        ).mappings().all()

        return {
            "generated_at": now.isoformat(),
            "metrics": {
                "total_articles": int(total_articles),
                "articles_last_24_hours": int(recent_articles),
                "active_sources": int(active_sources),
                "categories": int(categories),
                "topics": int(topics),
                "entities": int(entities),
            },
            "trending_topics": [
                {
                    "topic": row["name"],
                    "article_count": int(row["article_count"]),
                }
                for row in trend_rows
            ],
        }

    finally:
        db.close()
