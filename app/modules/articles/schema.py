from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.articles.model import ArticleStatus


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., max_length=500)
    cover_image_url: str | None = Field(None, max_length=500)
    status: ArticleStatus = ArticleStatus.DRAFT


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1)
    category: str | None = Field(None, min_length=1, max_length=100)
    summary: str | None = Field(None, max_length=500)
    cover_image_url: str | None = Field(None, max_length=500)
    status: ArticleStatus | None = None


class ArticleListItem(BaseModel):
    id: int
    title: str
    summary: str | None
    status: ArticleStatus
    created_at: datetime
    url: str


class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: str
    summary: str | None
    cover_image_url: str | None
    status: ArticleStatus
    author_id: int
    author_name: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def resolve_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "title": data.title,
            "content": data.content,
            "category": data.category,
            "summary": data.summary,
            "cover_image_url": data.cover_image_url,
            "status": data.status,
            "author_id": data.author_id,
            "author_name": data.author.name if data.author else "",
            "created_at": data.created_at,
            "updated_at": data.updated_at,
        }
