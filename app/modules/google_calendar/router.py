import logging

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.database import get_db
from app.modules.appointments.controller import AppointmentController
from app.modules.appointments.schema import AppointmentSyncResult
from app.modules.google_calendar.controller import GoogleCalendarController
from app.modules.google_calendar.google_service import GoogleCalendarApiClient
from app.modules.google_calendar.schema import GoogleAuthUrlRead, GoogleStatusRead
from app.modules.users.model import User
from app.shared.auth_deps import get_current_user
from app.shared.google_deps import get_google_calendar_client
from app.shared.responses import SuccessResponse, error_responses, ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/google", tags=["Google Calendar"])


@router.get(
    "/auth-url",
    response_model=SuccessResponse[GoogleAuthUrlRead],
    responses=error_responses(401),
    summary="Retorna a URL de consentimento OAuth do Google",
)
def get_google_auth_url(
    db: Session = Depends(get_db),
    client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[GoogleAuthUrlRead]:
    return ok(GoogleCalendarController(db, client).get_auth_url(current_user.id))


@router.get(
    "/callback",
    summary="Callback OAuth do Google — troca o code por tokens",
)
def google_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
    client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
) -> RedirectResponse:
    base = get_settings().frontend_url.rstrip("/")
    if error or not code or not state:
        return RedirectResponse(
            f"{base}/?google_calendar=error", status_code=status.HTTP_302_FOUND
        )
    try:
        GoogleCalendarController(db, client).handle_callback(code, state)
        target = f"{base}/?google_calendar=connected"
    except Exception:
        logger.exception("Google OAuth callback failed")
        target = f"{base}/?google_calendar=error"
    return RedirectResponse(target, status_code=status.HTTP_302_FOUND)


@router.get(
    "/status",
    response_model=SuccessResponse[GoogleStatusRead],
    responses=error_responses(401),
    summary="Indica se o usuário tem o Google Calendar conectado",
)
def get_google_status(
    db: Session = Depends(get_db),
    client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[GoogleStatusRead]:
    return ok(GoogleCalendarController(db, client).get_status(current_user.id))


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401),
    summary="Desconecta o Google Calendar do usuário",
)
def disconnect_google(
    db: Session = Depends(get_db),
    client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> Response:
    GoogleCalendarController(db, client).disconnect(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/sync-all",
    response_model=SuccessResponse[AppointmentSyncResult],
    responses=error_responses(401, 409, 503),
    summary="Sincroniza ao Google os compromissos futuros ainda não enviados",
)
def sync_all_appointments(
    db: Session = Depends(get_db),
    client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[AppointmentSyncResult]:
    return ok(AppointmentController(db, client).sync_all_to_google(current_user))
