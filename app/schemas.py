from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    summary: str | None = None
    category: str
    published_at: datetime | None = None
    source_id: int


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    feed_url: str
    category: str
    country: str | None = None
    source_type: str | None = None
    active: bool
    article_count: int
