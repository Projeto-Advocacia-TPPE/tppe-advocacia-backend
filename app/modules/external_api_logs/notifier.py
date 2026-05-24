from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config.settings import get_settings
from app.modules.external_api_logs.model import ExternalApiLog
from app.modules.external_api_logs.repository import ExternalApiLogRepository
from app.modules.notifications.schema import EventType
from app.modules.notifications.service import NotificationService
from app.modules.users.repository import UserRepository
from app.shared.types import Role


class ExternalApiFailureNotifier:
    def __init__(
        self,
        users: UserRepository,
        notifications: NotificationService,
        log_repository: ExternalApiLogRepository,
        throttle_minutes: int | None = None,
    ) -> None:
        self.users = users
        self.notifications = notifications
        self.log_repository = log_repository
        self.throttle_minutes = (
            get_settings().integration_failure_email_throttle_minutes
            if throttle_minutes is None
            else throttle_minutes
        )

    def notify_failure(self, log: ExternalApiLog) -> int:
        now = datetime.now(timezone.utc)
        if self._is_throttled(log, now):
            return 0

        admins, _ = self.users.get_all(
            role=Role.ADMIN,
            is_active=True,
            page=1,
            limit=1000,
        )
        if not admins:
            return 0

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

    def _is_throttled(self, log: ExternalApiLog, now: datetime) -> bool:
        if self.throttle_minutes == 0:
            return False
        since = now - timedelta(minutes=self.throttle_minutes)
        return (
            self.log_repository.count_recent_failures(
                provider=log.provider,
                operation=log.operation,
                since=since,
                exclude_id=log.id,
            )
            > 0
        )
