from fastapi import APIRouter, Depends

from app.modules.notifications.deps import get_notification_service
from app.modules.notifications.schema import PreferencesRead, PreferencesUpdate
from app.modules.notifications.service import NotificationService
from app.modules.users.model import User
from app.shared.auth_deps import get_current_user
from app.shared.responses import SuccessResponse, error_responses, ok

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/preferences",
    response_model=SuccessResponse[PreferencesRead],
    responses=error_responses(401),
    summary="Get notification preferences for the authenticated user",
)
def get_preferences(
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PreferencesRead]:
    prefs = service.get_preferences(current_user.id)
    return ok(PreferencesRead(preferences=prefs))


@router.patch(
    "/preferences",
    response_model=SuccessResponse[PreferencesRead],
    responses=error_responses(401, 422),
    summary="Update notification preferences for the authenticated user",
)
def update_preferences(
    payload: PreferencesUpdate,
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PreferencesRead]:
    prefs = service.update_preferences(current_user.id, payload.preferences)
    return ok(PreferencesRead(preferences=prefs))
