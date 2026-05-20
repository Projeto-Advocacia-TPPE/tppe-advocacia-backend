from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.forensic_holidays.controller import ForensicHolidayController
from app.modules.forensic_holidays.schema import (
    HolidayCreate,
    HolidayRead,
    HolidayUpdate,
)
from app.modules.users.model import User
from app.shared.auth_deps import get_current_user, require_admin
from app.shared.responses import (
    PaginatedResponse,
    SuccessResponse,
    error_responses,
    ok,
    paginated,
)

router = APIRouter(tags=["Forensic Holidays"])


@router.get(
    "/forensic-holidays",
    response_model=PaginatedResponse[HolidayRead],
    responses=error_responses(401),
    summary="Lista feriados forenses (filtros: year, court, comarca)",
)
def list_holidays(
    year: int | None = Query(None, ge=1900, le=2100),
    court: str | None = Query(None, max_length=50),
    comarca: str | None = Query(None, max_length=120),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[HolidayRead]:
    items, total = ForensicHolidayController(db).list(
        year=year, court=court, comarca=comarca, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)


@router.post(
    "/forensic-holidays",
    response_model=SuccessResponse[HolidayRead],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401, 403, 422),
    summary="Cria um novo feriado forense (admin)",
)
def create_holiday(
    payload: HolidayCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SuccessResponse[HolidayRead]:
    return ok(ForensicHolidayController(db).create(payload))


@router.patch(
    "/forensic-holidays/{holiday_id}",
    response_model=SuccessResponse[HolidayRead],
    responses=error_responses(401, 403, 404, 422),
    summary="Atualiza um feriado forense (admin)",
)
def update_holiday(
    holiday_id: int,
    payload: HolidayUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SuccessResponse[HolidayRead]:
    return ok(ForensicHolidayController(db).update(holiday_id, payload))


@router.delete(
    "/forensic-holidays/{holiday_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404),
    summary="Remove um feriado forense (admin)",
)
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Response:
    ForensicHolidayController(db).delete(holiday_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
