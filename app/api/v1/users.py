from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.controllers.user_controller import UserController
from app.db.database import get_db
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.utils.auth_deps import require_admin
from app.utils.responses import PaginatedResponse, SuccessResponse, error_responses, ok, paginated

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    responses=error_responses(401, 403),
    summary="List users with filters and pagination",
)
def list_users(
    role: Role | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> PaginatedResponse[UserRead]:
    items, total = UserController(db).list_users(
        role=role, is_active=is_active, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)


@router.post(
    "",
    status_code=201,
    response_model=SuccessResponse[UserRead],
    responses=error_responses(401, 403, 409, 422),
    summary="Create a new user",
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SuccessResponse[UserRead]:
    return ok(UserController(db).create_user(payload))


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserRead],
    responses=error_responses(401, 403, 404),
    summary="Get a user by ID",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SuccessResponse[UserRead]:
    return ok(UserController(db).get_user(user_id))


@router.patch(
    "/{user_id}",
    response_model=SuccessResponse[UserRead],
    responses=error_responses(401, 403, 404, 409, 422),
    summary="Update user data, role, or status",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SuccessResponse[UserRead]:
    return ok(UserController(db).update_user(user_id, payload))
