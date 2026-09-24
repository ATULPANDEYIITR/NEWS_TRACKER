from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models.source import Source


db = SessionLocal()

try:

    total = db.scalar(
        select(func.count(Source.id))
    ) or 0

    configured = db.scalar(
        select(func.count(Source.id))
        .where(
            Source.is_active.is_(True),
            Source.feed_url.is_not(None),
        )
    ) or 0

    active = db.scalar(
        select(func.count(Source.id))
        .where(
            Source.is_active.is_(True)
        )
    ) or 0

    print()
    print(
        "=========================================="
    )
    print(
        "SOURCE REGISTRY SUMMARY"
    )
    print(
        "=========================================="
    )
    print(
        f"Total sources          : {total}"
    )
    print(
        f"Active sources         : {active}"
    )
    print(
        f"Sources with live feed : {configured}"
    )

finally:
    db.close()
