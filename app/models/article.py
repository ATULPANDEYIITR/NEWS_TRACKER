
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Article(Base):
    __tablename__ = "articles"

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "canonical_url",
            name="uq_article_source_canonical_url",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    headline: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    canonical_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    original_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    author: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    normalized_title_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    language: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    region: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    source = relationship("Source", backref="articles")

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, headline='{self.headline[:60]}')>"
