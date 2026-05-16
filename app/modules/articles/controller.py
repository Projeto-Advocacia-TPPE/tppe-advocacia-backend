from sqlalchemy.orm import Session
from starlette.requests import Request

from app.modules.articles.repository import ArticleRepository
from app.modules.articles.schema import (
    ArticleCreate,
    ArticleListItem,
    ArticleRead,
    ArticleUpdate,
)
from app.modules.articles.service import ArticleService
from app.modules.users.model import User


class ArticleController:
    def __init__(self, db: Session) -> None:
        self.service = ArticleService(ArticleRepository(db))

    def create(self, payload: ArticleCreate, author: User) -> ArticleRead:
        return self.service.create(payload, author)

    def update(self, article_id: int, payload: ArticleUpdate) -> ArticleRead:
        return self.service.update(article_id, payload)

    def get_by_id(self, article_id: int) -> ArticleRead:
        return self.service.get_published_by_id(article_id)

    def get_preview(self, article_id: int) -> ArticleRead:
        return self.service.get_preview(article_id)

    def list_published(
        self, request: Request, page: int = 1, limit: int = 20
    ) -> tuple[list[ArticleListItem], int]:
        return self.service.list_published(request=request, page=page, limit=limit)

    def list_all(
        self, request: Request, page: int = 1, limit: int = 20
    ) -> tuple[list[ArticleListItem], int]:
        return self.service.list_all(request=request, page=page, limit=limit)
