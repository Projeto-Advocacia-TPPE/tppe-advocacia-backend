from fastapi import APIRouter, Depends, Query

from app.modules.users.deps import get_user_service
from app.modules.users.model import User
from app.modules.users.schema import UserCreate, UserRead, UserUpdate
from app.modules.users.service import UserService
from app.shared.auth_deps import require_admin
from app.shared.responses import (
    PaginatedResponse,
    SuccessResponse,
    error_responses,
    ok,
    paginated,
)
from app.shared.types import Role

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
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
) -> PaginatedResponse[UserRead]:
    items, total = service.list_users(role=role, is_active=is_active, page=page, limit=limit)
    return paginated(
        [UserRead.model_validate(u) for u in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post(
    "",
    status_code=201,
    response_model=SuccessResponse[UserRead],
    responses=error_responses(401, 403, 409, 422),
    summary="Create a new user",
)
def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse[UserRead]:
    return ok(UserRead.model_validate(service.create_user(payload, created_by=current_user)))


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserRead],
    responses=error_responses(401, 403, 404),
    summary="Get a user by ID",
)
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
) -> SuccessResponse[UserRead]:
    return ok(UserRead.model_validate(service.get_user(user_id)))


@router.patch(
    "/{user_id}",
    response_model=SuccessResponse[UserRead],
    responses=error_responses(401, 403, 404, 409, 422),
    summary="Update user data, role, or status",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse[UserRead]:
    return ok(UserRead.model_validate(service.update_user(user_id, payload, updated_by=current_user)))
