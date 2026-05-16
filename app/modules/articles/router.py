from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.articles.controller import ArticleController
from app.modules.articles.schema import (
    ArticleCreate,
    ArticleListItem,
    ArticleRead,
    ArticleUpdate,
)
from app.modules.users.model import User
from app.shared.auth_deps import get_current_user
from app.shared.responses import (
    PaginatedResponse,
    SuccessResponse,
    error_responses,
    ok,
    paginated,
)

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post(
    "",
    status_code=201,
    response_model=SuccessResponse[ArticleRead],
    responses=error_responses(401, 422),
    summary="Create a new article",
)
def create_article(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[ArticleRead]:
    return ok(ArticleController(db).create(payload, author=current_user))


@router.patch(
    "/{article_id}",
    response_model=SuccessResponse[ArticleRead],
    responses=error_responses(401, 404, 422),
    summary="Update an article",
)
def update_article(
    article_id: int,
    payload: ArticleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SuccessResponse[ArticleRead]:
    return ok(ArticleController(db).update(article_id, payload))


@router.get(
    "/admin",
    response_model=PaginatedResponse[ArticleListItem],
    responses=error_responses(401),
    summary="List all articles including drafts (authenticated)",
)
def list_all_articles(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[ArticleListItem]:
    items, total = ArticleController(db).list_all(
        request=request, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)


@router.get(
    "/{article_id}/preview",
    response_model=SuccessResponse[ArticleRead],
    responses=error_responses(401, 404),
    summary="Preview an article regardless of status",
)
def preview_article(
    article_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SuccessResponse[ArticleRead]:
    return ok(ArticleController(db).get_preview(article_id))


@router.get(
    "/{article_id}",
    response_model=SuccessResponse[ArticleRead],
    responses=error_responses(404),
    summary="Get a published article by ID",
)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
) -> SuccessResponse[ArticleRead]:
    return ok(ArticleController(db).get_by_id(article_id))


@router.get(
    "",
    response_model=PaginatedResponse[ArticleListItem],
    summary="List published articles",
)
def list_articles(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ArticleListItem]:
    items, total = ArticleController(db).list_published(
        request=request, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)
