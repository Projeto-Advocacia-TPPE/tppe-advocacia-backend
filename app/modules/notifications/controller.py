from sqlalchemy.orm import Session

from app.modules.email.protocol import EmailService
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.schema import EventType
from app.modules.notifications.service import NotificationService
from app.modules.users.repository import UserRepository


class NotificationController:
    def __init__(self, db: Session, email: EmailService) -> None:
        self.service = NotificationService(
            NotificationPreferenceRepository(db),
            UserRepository(db),
            email,
        )

    def get_preferences(self, user_id: int) -> dict[EventType, bool]:
        return self.service.get_preferences(user_id)

    def update_preferences(
        self, user_id: int, prefs: dict[EventType, bool]
    ) -> dict[EventType, bool]:
        return self.service.update_preferences(user_id, prefs)
