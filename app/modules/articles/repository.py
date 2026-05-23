from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.articles.model import Article, ArticleStatus


class ArticleRepository:
    """Este repositório nunca comita. Operações de escrita usam db.add + db.flush
    e o Service que orquestra a transação fecha com unit_of_work."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        title: str,
        content: str,
        category: str,
        author_id: int,
        cover_image_url: str | None,
        status: ArticleStatus,
        summary: str | None = None,
    ) -> Article:
        article = Article(
            title=title,
            content=content,
            category=category,
            author_id=author_id,
            cover_image_url=cover_image_url,
            status=status,
            summary=summary,
        )
        self.db.add(article)
        self.db.flush()
        return article

    def get_by_id(self, article_id: int) -> Article | None:
        return self.db.scalars(select(Article).where(Article.id == article_id)).first()

    def get_published(
        self, page: int = 1, limit: int = 20
    ) -> tuple[list[Article], int]:
        base = select(Article).where(Article.status == ArticleStatus.PUBLISHED)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        articles = list(
            self.db.scalars(
                base.order_by(Article.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()
        )
        return articles, total

    def get_all(self, page: int = 1, limit: int = 20) -> tuple[list[Article], int]:
        base = select(Article)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        articles = list(
            self.db.scalars(
                base.order_by(Article.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()
        )
        return articles, total

    def update(self, article: Article, data: dict) -> Article:
        for key, value in data.items():
            setattr(article, key, value)
        self.db.flush()
        return article
