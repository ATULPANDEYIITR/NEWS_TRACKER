from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)

    name = Column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )

    url = Column(
        String(1000),
        nullable=False,
    )

    feed_url = Column(
        String(1000),
        nullable=False,
    )

    category = Column(
        String(100),
        nullable=False,
        index=True,
    )

    country = Column(
        String(100),
        nullable=True,
    )

    source_type = Column(
        String(100),
        nullable=True,
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_checked = Column(
        DateTime,
        nullable=True,
    )

    last_success = Column(
        DateTime,
        nullable=True,
    )

    last_error = Column(
        Text,
        nullable=True,
    )

    article_count = Column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)

    source_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    title = Column(
        String(1000),
        nullable=False,
    )

    url = Column(
        String(2000),
        nullable=False,
    )

    normalized_url = Column(
        String(2000),
        nullable=False,
    )

    summary = Column(
        Text,
        nullable=True,
    )

    category = Column(
        String(100),
        nullable=False,
        index=True,
    )

    published_at = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    collected_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    content_hash = Column(
        String(64),
        nullable=False,
        index=True,
    )

    author = Column(
        String(300),
        nullable=True,
    )

    image_url = Column(
        String(2000),
        nullable=True,
    )

    language = Column(
        String(50),
        default="en",
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "normalized_url",
            name="uq_article_normalized_url",
        ),
    )
