from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.appointments.controller import AppointmentController
from app.modules.appointments.model import AppointmentType
from app.modules.appointments.schema import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentUpdate,
)
from app.modules.google_calendar.google_service import GoogleCalendarApiClient
from app.modules.users.model import User
from app.shared.auth_deps import get_current_user
from app.shared.google_deps import get_google_calendar_client
from app.shared.responses import (
    PaginatedResponse,
    SuccessResponse,
    error_responses,
    ok,
    paginated,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[AppointmentRead],
    responses=error_responses(401, 422),
    summary="Cria um compromisso na agenda",
)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    google_client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[AppointmentRead]:
    return ok(
        AppointmentController(db, google_client).create_appointment(
            payload, current_user
        )
    )


@router.get(
    "",
    response_model=PaginatedResponse[AppointmentRead],
    responses=error_responses(401),
    summary="Lista os compromissos do usuário autenticado, com filtros",
)
def list_appointments(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    type: AppointmentType | None = Query(None),
    client_id: int | None = Query(None),
    process_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    google_client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[AppointmentRead]:
    items, total = AppointmentController(db, google_client).list_appointments(
        current_user,
        date_from=date_from,
        date_to=date_to,
        type=type,
        client_id=client_id,
        process_id=process_id,
        page=page,
        limit=limit,
    )
    return paginated(items, total=total, page=page, limit=limit)


@router.get(
    "/{appointment_id}",
    response_model=SuccessResponse[AppointmentRead],
    responses=error_responses(401, 403, 404),
    summary="Retorna os detalhes de um compromisso",
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    google_client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[AppointmentRead]:
    return ok(
        AppointmentController(db, google_client).get_appointment(
            appointment_id, current_user
        )
    )


@router.patch(
    "/{appointment_id}",
    response_model=SuccessResponse[AppointmentRead],
    responses=error_responses(401, 403, 404, 422),
    summary="Atualiza parcialmente um compromisso",
)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    google_client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[AppointmentRead]:
    return ok(
        AppointmentController(db, google_client).update_appointment(
            appointment_id, payload, current_user
        )
    )


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404),
    summary="Remove um compromisso",
)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    google_client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> Response:
    AppointmentController(db, google_client).delete_appointment(
        appointment_id, current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
