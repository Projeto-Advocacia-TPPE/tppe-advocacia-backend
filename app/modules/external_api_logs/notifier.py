from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config.settings import get_settings
from app.modules.external_api_logs.model import ExternalApiLog
from app.modules.notifications.schema import EventType
from app.modules.notifications.service import NotificationService
from app.modules.users.repository import UserRepository
from app.shared.types import Role

_last_notification_at: dict[tuple[str, str], datetime] = {}


def clear_external_api_failure_notification_throttle() -> None:
    _last_notification_at.clear()


class ExternalApiFailureNotifier:
    def __init__(
        self,
        users: UserRepository,
        notifications: NotificationService,
        throttle_minutes: int | None = None,
    ) -> None:
        self.users = users
        self.notifications = notifications
        self.throttle_minutes = (
            get_settings().integration_failure_email_throttle_minutes
            if throttle_minutes is None
            else throttle_minutes
        )

    def notify_failure(self, log: ExternalApiLog) -> int:
        key = (log.provider.value, log.operation.value)
        now = datetime.now(timezone.utc)
        if self._is_throttled(key, now):
            return 0

        admins, _ = self.users.get_all(
            role=Role.ADMIN,
            is_active=True,
            page=1,
            limit=1000,
        )
        if not admins:
            return 0

        _last_notification_at[key] = now
        payload = {
            "provider": log.provider.value,
            "operation": log.operation.value,
            "http_status": log.http_status,
            "error_code": log.error_code,
            "error_message": log.error_message,
            "request_identifier": log.request_identifier,
            "tribunal_alias": log.tribunal_alias,
        }
        for admin in admins:
            self.notifications.notify(
                user_id=admin.id,
                event_type=EventType.EXTERNAL_API_FAILURE,
                payload=payload,
            )
        return len(admins)

    def _is_throttled(self, key: tuple[str, str], now: datetime) -> bool:
        if self.throttle_minutes == 0:
            return False

        last_notification = _last_notification_at.get(key)
        if last_notification is None:
            return False

        return now - last_notification < timedelta(minutes=self.throttle_minutes)
