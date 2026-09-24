from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class AnalyticalScore(Base):
    __tablename__ = "analytical_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    conflict_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    geopolitical_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    economic_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    technology_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    climate_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    wellness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    classification: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    evidence_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
