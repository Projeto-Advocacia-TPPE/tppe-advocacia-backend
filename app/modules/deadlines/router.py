from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.deadlines.controller import DeadlineController
from app.modules.deadlines.schema import (
    DeadlineAlertRead,
    DeadlineCalculateRequest,
    DeadlineCalculateResponse,
    DeadlineCreate,
    DeadlineRead,
    DeadlineUpdate,
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

router = APIRouter(tags=["Deadlines"])


@router.post(
    "/deadlines/calculate",
    response_model=SuccessResponse[DeadlineCalculateResponse],
    responses=error_responses(401, 422),
    summary="Calcula data-limite em dias úteis sem persistir",
)
def calculate_deadline(
    payload: DeadlineCalculateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SuccessResponse[DeadlineCalculateResponse]:
    return ok(DeadlineController(db).calculate(payload))


@router.post(
    "/processes/{process_id}/deadlines",
    response_model=SuccessResponse[DeadlineRead],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401, 404, 422),
    summary="Cria prazo persistido vinculado ao processo",
)
def create_deadline(
    process_id: int,
    payload: DeadlineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[DeadlineRead]:
    return ok(
        DeadlineController(db).create_for_process(
            process_id, payload, current_user=current_user
        )
    )


@router.get(
    "/processes/{process_id}/deadlines",
    response_model=PaginatedResponse[DeadlineRead],
    responses=error_responses(401, 404),
    summary="Lista prazos de um processo",
)
def list_deadlines(
    process_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[DeadlineRead]:
    items, total = DeadlineController(db).list_by_process(
        process_id, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)


@router.patch(
    "/deadlines/{deadline_id}",
    response_model=SuccessResponse[DeadlineRead],
    responses=error_responses(401, 404, 422),
    summary="Atualiza prazo (recalcula due_date se start/business_days/comarca mudarem)",
)
def update_deadline(
    deadline_id: int,
    payload: DeadlineUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SuccessResponse[DeadlineRead]:
    return ok(DeadlineController(db).update(deadline_id, payload))


@router.delete(
    "/deadlines/{deadline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 404),
    summary="Remove um prazo",
)
def delete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    DeadlineController(db).delete(deadline_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/processes/{process_id}/deadlines/{deadline_id}/alerts",
    response_model=SuccessResponse[list[DeadlineAlertRead]],
    responses=error_responses(401, 403, 404),
    summary="Lista o histórico de alertas disparados de um prazo (admin/autor)",
)
def list_deadline_alerts(
    process_id: int,
    deadline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[DeadlineAlertRead]]:
    return ok(DeadlineController(db).list_alerts(process_id, deadline_id, current_user))
