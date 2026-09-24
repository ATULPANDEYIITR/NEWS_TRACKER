from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.article import Article
from app.models.article_category import ArticleCategory
from app.models.article_entity import ArticleEntity
from app.models.article_topic import ArticleTopic
from app.models.category import Category
from app.models.entity import Entity
from app.models.one_line_news import OneLineNews
from app.models.source import Source
from app.models.summary import Summary
from app.models.topic import Topic
from app.models.analytical_score import AnalyticalScore

router = APIRouter(
    prefix="/api",
    tags=["News"],
)


@router.get("/sources")
def get_sources(
    db: Session = Depends(get_db),
    active_only: bool = True,
    limit: int = Query(default=200, ge=1, le=500),
) -> list[dict[str, Any]]:
    query = db.query(Source)

    if active_only:
        query = query.filter(Source.is_active.is_(True))

    sources = (
        query
        .order_by(Source.name.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": source.id,
            "name": source.name,
            "website_url": source.website_url,
            "feed_url": source.feed_url,
            "country": source.country,
            "region": source.region,
            "language": source.language,
            "source_type": source.source_type,
            "is_active": source.is_active,
        }
        for source in sources
    ]


@router.get("/sources/{source_id}")
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    source = db.get(Source, source_id)

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    article_count = (
        db.query(func.count(Article.id))
        .filter(Article.source_id == source.id)
        .scalar()
    ) or 0

    return {
        "id": source.id,
        "name": source.name,
        "website_url": source.website_url,
        "feed_url": source.feed_url,
        "country": source.country,
        "region": source.region,
        "language": source.language,
        "source_type": source.source_type,
        "description": source.description,
        "is_active": source.is_active,
        "article_count": article_count,
    }


@router.get("/categories")
def get_categories(
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = (
        db.query(
            Category.id,
            Category.name,
            func.count(ArticleCategory.article_id).label("article_count"),
        )
        .outerjoin(
            ArticleCategory,
            ArticleCategory.category_id == Category.id,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.count(ArticleCategory.article_id).desc())
        .all()
    )

    return [
        {
            "id": row.id,
            "name": row.name,
            "article_count": row.article_count,
        }
        for row in rows
    ]


@router.get("/topics")
def get_topics(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    rows = (
        db.query(
            Topic.id,
            Topic.name,
            func.count(ArticleTopic.article_id).label("article_count"),
        )
        .outerjoin(
            ArticleTopic,
            ArticleTopic.topic_id == Topic.id,
        )
        .group_by(Topic.id, Topic.name)
        .order_by(func.count(ArticleTopic.article_id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "name": row.name,
            "article_count": row.article_count,
        }
        for row in rows
    ]


@router.get("/entities")
def get_entities(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    rows = (
        db.query(
            Entity.id,
            Entity.name,
            Entity.entity_type,
            func.count(ArticleEntity.article_id).label("article_count"),
        )
        .outerjoin(
            ArticleEntity,
            ArticleEntity.entity_id == Entity.id,
        )
        .group_by(
            Entity.id,
            Entity.name,
            Entity.entity_type,
        )
        .order_by(func.count(ArticleEntity.article_id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "name": row.name,
            "entity_type": row.entity_type,
            "article_count": row.article_count,
        }
        for row in rows
    ]


@router.get("/articles")
def get_articles(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    category: str | None = None,
    source: str | None = None,
    country: str | None = None,
    region: str | None = None,
    language: str | None = None,
    keyword: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:

    query = (
        db.query(Article)
        .join(Source, Article.source_id == Source.id)
    )

    if category:
        query = (
            query
            .join(
                ArticleCategory,
                ArticleCategory.article_id == Article.id,
            )
            .join(
                Category,
                Category.id == ArticleCategory.category_id,
            )
            .filter(Category.name.ilike(category))
        )

    if source:
        query = query.filter(Source.name.ilike(f"%{source}%"))

    if country:
        query = query.filter(Article.country.ilike(f"%{country}%"))

    if region:
        query = query.filter(Article.region.ilike(f"%{region}%"))

    if language:
        query = query.filter(Article.language.ilike(f"%{language}%"))

    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.filter(
            or_(
                Article.headline.ilike(keyword_filter),
                Article.description.ilike(keyword_filter),
                Article.content.ilike(keyword_filter),
            )
        )

    if start_date:
        query = query.filter(Article.published_at >= start_date)

    if end_date:
        query = query.filter(Article.published_at <= end_date)

    total = query.distinct().count()

    articles = (
        query
        .distinct()
        .order_by(
            Article.published_at.desc().nullslast(),
            Article.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []

    for article in articles:
        source_obj = db.get(Source, article.source_id)

        results.append(
            {
                "id": article.id,
                "headline": article.headline,
                "description": article.description,
                "published_at": (
                    article.published_at.isoformat()
                    if article.published_at
                    else None
                ),
                "collected_at": (
                    article.collected_at.isoformat()
                    if article.collected_at
                    else None
                ),
                "author": article.author,
                "language": article.language,
                "country": article.country,
                "region": article.region,
                "source": {
                    "id": source_obj.id if source_obj else None,
                    "name": source_obj.name if source_obj else None,
                    "website_url": (
                        source_obj.website_url
                        if source_obj
                        else None
                    ),
                },
                "original_url": (
                    article.original_url or article.canonical_url
                ),
            }
        )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size,
        "articles": results,
    }


@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:

    article = db.get(Article, article_id)

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    source = db.get(Source, article.source_id)

    categories = (
        db.query(Category)
        .join(
            ArticleCategory,
            ArticleCategory.category_id == Category.id,
        )
        .filter(ArticleCategory.article_id == article.id)
        .all()
    )

    topics = (
        db.query(Topic)
        .join(
            ArticleTopic,
            ArticleTopic.topic_id == Topic.id,
        )
        .filter(ArticleTopic.article_id == article.id)
        .all()
    )

    entities = (
        db.query(Entity)
        .join(
            ArticleEntity,
            ArticleEntity.entity_id == Entity.id,
        )
        .filter(ArticleEntity.article_id == article.id)
        .all()
    )

    summary = (
        db.query(Summary)
        .filter(Summary.article_id == article.id)
        .first()
    )

    one_line = (
        db.query(OneLineNews)
        .filter(OneLineNews.article_id == article.id)
        .first()
    )

    analytical = (
        db.query(AnalyticalScore)
        .filter(AnalyticalScore.article_id == article.id)
        .first()
    )

    return {
        "id": article.id,
        "headline": article.headline,
        "description": article.description,
        "content": article.content,
        "author": article.author,
        "published_at": (
            article.published_at.isoformat()
            if article.published_at
            else None
        ),
        "collected_at": (
            article.collected_at.isoformat()
            if article.collected_at
            else None
        ),
        "language": article.language,
        "country": article.country,
        "region": article.region,
        "original_url": (
            article.original_url or article.canonical_url
        ),
        "source": (
            {
                "id": source.id,
                "name": source.name,
                "website_url": source.website_url,
                "country": source.country,
                "region": source.region,
                "language": source.language,
            }
            if source
            else None
        ),
        "categories": [
            {
                "id": category.id,
                "name": category.name,
            }
            for category in categories
        ],
        "topics": [
            {
                "id": topic.id,
                "name": topic.name,
            }
            for topic in topics
        ],
        "entities": [
            {
                "id": entity.id,
                "name": entity.name,
                "entity_type": entity.entity_type,
            }
            for entity in entities
        ],
        "summary": (
            {
                "short_summary": summary.short_summary,
                "key_points": summary.key_points,
                "summary_method": summary.summary_method,
            }
            if summary
            else None
        ),
        "one_line_news": (
            one_line.one_line
            if one_line
            else None
        ),
        "analytical_scores": (
            {
                "importance": analytical.importance,
                "conflict": analytical.conflict,
                "geopolitical": analytical.geopolitical,
                "economic": analytical.economic,
                "technology": analytical.technology,
                "climate": analytical.climate,
                "wellness": analytical.wellness,
                "classification": analytical.classification,
                "evidence_note": analytical.evidence_note,
            }
            if analytical
            else None
        ),
    }


@router.get("/one-line-news")
def get_one_line_news(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    category: str | None = None,
) -> list[dict[str, Any]]:

    query = (
        db.query(
            OneLineNews,
            Article,
            Source,
        )
        .join(
            Article,
            Article.id == OneLineNews.article_id,
        )
        .join(
            Source,
            Source.id == Article.source_id,
        )
    )

    if category:
        query = (
            query
            .join(
                ArticleCategory,
                ArticleCategory.article_id == Article.id,
            )
            .join(
                Category,
                Category.id == ArticleCategory.category_id,
            )
            .filter(Category.name.ilike(category))
        )

    rows = (
        query
        .order_by(
            Article.published_at.desc().nullslast(),
            Article.id.desc(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "article_id": one_line.article_id,
            "headline": article.headline,
            "one_line": one_line.one_line,
            "source": source.name,
            "country": article.country,
            "region": article.region,
            "published_at": (
                article.published_at.isoformat()
                if article.published_at
                else None
            ),
            "original_url": (
                article.original_url or article.canonical_url
            ),
        }
        for one_line, article, source in rows
    ]


@router.get("/search")
def search_news(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:

    search_term = f"%{q}%"

    articles = (
        db.query(Article)
        .filter(
            or_(
                Article.headline.ilike(search_term),
                Article.description.ilike(search_term),
                Article.content.ilike(search_term),
            )
        )
        .order_by(
            Article.published_at.desc().nullslast(),
            Article.id.desc(),
        )
        .limit(limit)
        .all()
    )

    results = []

    for article in articles:
        source = db.get(Source, article.source_id)

        results.append(
            {
                "id": article.id,
                "headline": article.headline,
                "source": source.name if source else None,
                "country": article.country,
                "region": article.region,
                "published_at": (
                    article.published_at.isoformat()
                    if article.published_at
                    else None
                ),
                "original_url": (
                    article.original_url or article.canonical_url
                ),
            }
        )

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }
