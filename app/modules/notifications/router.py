from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.email.protocol import EmailService
from app.modules.notifications.controller import NotificationController
from app.modules.notifications.schema import PreferencesRead, PreferencesUpdate
from app.modules.users.model import User
from app.shared.auth_deps import get_current_user
from app.shared.email_deps import get_email_service
from app.shared.responses import SuccessResponse, error_responses, ok

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/preferences",
    response_model=SuccessResponse[PreferencesRead],
    responses=error_responses(401),
    summary="Get notification preferences for the authenticated user",
)
def get_preferences(
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PreferencesRead]:
    prefs = NotificationController(db, email).get_preferences(current_user.id)
    return ok(PreferencesRead(preferences=prefs))


@router.patch(
    "/preferences",
    response_model=SuccessResponse[PreferencesRead],
    responses=error_responses(401, 422),
    summary="Update notification preferences for the authenticated user",
)
def update_preferences(
    payload: PreferencesUpdate,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PreferencesRead]:
    prefs = NotificationController(db, email).update_preferences(
        current_user.id, payload.preferences
    )
    return ok(PreferencesRead(preferences=prefs))
