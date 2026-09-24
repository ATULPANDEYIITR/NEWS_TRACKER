from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.article import Article
from app.models.article_category import ArticleCategory
from app.models.category import Category
from app.models.source import Source

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("/overview")
def dashboard_overview(
    db: Session = Depends(get_db),
) -> dict[str, Any]:

    total_articles = db.query(func.count(Article.id)).scalar() or 0
    total_sources = db.query(func.count(Source.id)).scalar() or 0
    total_categories = db.query(func.count(Category.id)).scalar() or 0

    active_sources = (
        db.query(func.count(Source.id))
        .filter(Source.is_active.is_(True))
        .scalar()
        or 0
    )

    today_start = datetime.now(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    today_articles = (
        db.query(func.count(Article.id))
        .filter(Article.collected_at >= today_start)
        .scalar()
        or 0
    )

    last_24_hours = datetime.now(timezone.utc) - timedelta(hours=24)

    recent_articles = (
        db.query(func.count(Article.id))
        .filter(Article.collected_at >= last_24_hours)
        .scalar()
        or 0
    )

    categories = (
        db.query(
            Category.name,
            func.count(ArticleCategory.article_id).label("count"),
        )
        .outerjoin(
            ArticleCategory,
            ArticleCategory.category_id == Category.id,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.count(ArticleCategory.article_id).desc())
        .limit(15)
        .all()
    )

    sources = (
        db.query(
            Source.name,
            func.count(Article.id).label("count"),
        )
        .outerjoin(
            Article,
            Article.source_id == Source.id,
        )
        .group_by(Source.id, Source.name)
        .order_by(func.count(Article.id).desc())
        .limit(15)
        .all()
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "articles": total_articles,
            "sources": total_sources,
            "active_sources": active_sources,
            "categories": total_categories,
            "articles_today": today_articles,
            "articles_last_24_hours": recent_articles,
        },
        "top_categories": [
            {
                "name": row.name,
                "article_count": row.count,
            }
            for row in categories
        ],
        "top_sources": [
            {
                "name": row.name,
                "article_count": row.count,
            }
            for row in sources
        ],
    }


@router.get("/category/{category_name}")
def category_dashboard(
    category_name: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:

    category = (
        db.query(Category)
        .filter(Category.name.ilike(category_name))
        .first()
    )

    if category is None:
        return {
            "category": category_name,
            "article_count": 0,
            "articles": [],
        }

    articles = (
        db.query(Article)
        .join(
            ArticleCategory,
            ArticleCategory.article_id == Article.id,
        )
        .filter(
            ArticleCategory.category_id == category.id
        )
        .order_by(
            Article.published_at.desc().nullslast(),
            Article.id.desc(),
        )
        .limit(100)
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
        "category": category.name,
        "article_count": len(results),
        "articles": results,
    }
