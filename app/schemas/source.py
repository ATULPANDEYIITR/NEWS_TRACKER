from pydantic import BaseModel, ConfigDict, Field


class SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website_url: str = Field(min_length=1, max_length=1000)
    feed_url: str | None = Field(default=None, max_length=1000)
    country: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, max_length=50)
    source_type: str = Field(default="news", max_length=50)
    description: str | None = None
    is_active: bool = True


class SourceCreate(SourceBase):
    pass


class SourceResponse(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
