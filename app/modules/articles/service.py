from starlette.requests import Request

from app.modules.articles.model import ArticleStatus
from app.modules.articles.repository import ArticleRepository
from app.modules.articles.schema import (
    ArticleCreate,
    ArticleListItem,
    ArticleRead,
    ArticleUpdate,
)
from app.modules.users.model import User
from app.shared.exceptions import ArticleNotFoundError


class ArticleService:
    def __init__(self, repository: ArticleRepository) -> None:
        self.repository = repository

    def create(self, payload: ArticleCreate, author: User) -> ArticleRead:
        article = self.repository.create(
            title=payload.title,
            content=payload.content,
            category=payload.category,
            author_id=author.id,
            cover_image_url=payload.cover_image_url,
            status=payload.status,
            summary=payload.summary,
        )
        return self._to_read(article)

    def update(self, article_id: int, payload: ArticleUpdate) -> ArticleRead:
        article = self.repository.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError()
        data = payload.model_dump(exclude_none=True)
        updated = self.repository.update(article, data)
        return self._to_read(updated)

    def get_published_by_id(self, article_id: int) -> ArticleRead:
        article = self.repository.get_by_id(article_id)
        if article is None or article.status != ArticleStatus.PUBLISHED:
            raise ArticleNotFoundError()
        return self._to_read(article)

    def get_preview(self, article_id: int) -> ArticleRead:
        article = self.repository.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError()
        return self._to_read(article)

    def list_published(
        self, request: Request, page: int = 1, limit: int = 20
    ) -> tuple[list[ArticleListItem], int]:
        articles, total = self.repository.get_published(page=page, limit=limit)
        return [
            self._to_list_item(a, str(request.url_for("get_article", article_id=a.id)))
            for a in articles
        ], total

    def list_all(
        self, request: Request, page: int = 1, limit: int = 20
    ) -> tuple[list[ArticleListItem], int]:
        articles, total = self.repository.get_all(page=page, limit=limit)
        return [
            self._to_list_item(
                a, str(request.url_for("preview_article", article_id=a.id))
            )
            for a in articles
        ], total

    @staticmethod
    def _to_list_item(article, url: str) -> ArticleListItem:
        return ArticleListItem(
            id=article.id,
            title=article.title,
            summary=article.summary,
            status=article.status,
            created_at=article.created_at,
            url=url,
        )

    @staticmethod
    def _to_read(article) -> ArticleRead:
        return ArticleRead(
            id=article.id,
            title=article.title,
            content=article.content,
            category=article.category,
            summary=article.summary,
            cover_image_url=article.cover_image_url,
            status=article.status,
            author_id=article.author_id,
            author_name=article.author.name,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )
