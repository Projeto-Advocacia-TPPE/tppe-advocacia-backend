from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notifications.model import NotificationPreference
from app.modules.notifications.schema import EventType


class NotificationPreferenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user(self, user_id: int) -> list[NotificationPreference]:
        return list(
            self.db.scalars(
                select(NotificationPreference).where(
                    NotificationPreference.user_id == user_id
                )
            ).all()
        )

    def upsert_many(
        self, user_id: int, prefs: dict[EventType, bool]
    ) -> list[NotificationPreference]:
        existing = {p.event_type: p for p in self.get_by_user(user_id)}

        for event_type, enabled in prefs.items():
            row = existing.get(event_type)
            if row is None:
                self.db.add(
                    NotificationPreference(
                        user_id=user_id, event_type=event_type, enabled=enabled
                    )
                )
            elif row.enabled != enabled:
                row.enabled = enabled

        self.db.commit()
        return self.get_by_user(user_id)
