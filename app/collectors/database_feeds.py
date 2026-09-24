from __future__ import annotations

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.source import Source


def get_database_feeds() -> list[dict]:

    db = SessionLocal()

    try:

        sources = db.scalars(
            select(Source)
            .where(
                Source.is_active.is_(True),
                Source.feed_url.is_not(None),
            )
            .order_by(Source.name)
        ).all()

        feeds = []

        for source in sources:

            if not source.feed_url:
                continue

            feeds.append(
                {
                    "source_id": source.id,
                    "source_name": source.name,
                    "feed_url": source.feed_url,
                    "country": source.country,
                    "region": source.region,
                    "language": source.language,
                }
            )

        return feeds

    finally:
        db.close()


if __name__ == "__main__":

    feeds = get_database_feeds()

    print()
    print(
        "=========================================="
    )
    print(
        "DATABASE LIVE FEEDS"
    )
    print(
        "=========================================="
    )

    print(
        f"Configured database feeds: {len(feeds)}"
    )

    for feed in feeds:
        print(
            f"{feed['source_name']} | "
            f"{feed['feed_url']}"
        )
