from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class StoryCluster(Base):
    __tablename__ = "story_clusters"

    cluster_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    articles = relationship(
        "Article",
        backref="story_cluster",
    )

    def __repr__(self) -> str:
        return (
            f"<StoryCluster("
            f"cluster_id={self.cluster_id}, "
            f"title='{self.title}')>"
        )
