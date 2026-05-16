from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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

    model_config = ConfigDict(from_attributes=True)
