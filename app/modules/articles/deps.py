from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.articles.repository import ArticleRepository
from app.modules.articles.service import ArticleService


def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    return ArticleService(ArticleRepository(db))
