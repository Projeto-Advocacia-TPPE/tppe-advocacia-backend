import logging

from app.modules.email.protocol import EmailService
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.schema import EventType
from app.modules.notifications.templates import TEMPLATES
from app.modules.users.repository import UserRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        repository: NotificationPreferenceRepository,
        users: UserRepository,
        email: EmailService,
    ) -> None:
        self.repository = repository
        self.users = users
        self.email = email

    def get_preferences(self, user_id: int) -> dict[EventType, bool]:
        stored = {p.event_type: p.enabled for p in self.repository.get_by_user(user_id)}
        return {event: stored.get(event, True) for event in EventType}

    def update_preferences(
        self, user_id: int, prefs: dict[EventType, bool]
    ) -> dict[EventType, bool]:
        self.repository.upsert_many(user_id, prefs)
        return self.get_preferences(user_id)

    def notify(self, user_id: int, event_type: EventType, payload: dict) -> None:
        user = self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            return

        if not self.get_preferences(user_id)[event_type]:
            return

        renderer = TEMPLATES.get(event_type)
        if renderer is None:
            logger.warning("No template registered for event %s", event_type)
            return

        try:
            subject, html = renderer(payload)
            self.email.send(to=user.email, subject=subject, html=html)
        except Exception:
            logger.exception(
                "Failed to send notification email user_id=%s event=%s",
                user_id,
                event_type,
            )
