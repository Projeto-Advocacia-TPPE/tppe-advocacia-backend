from datetime import datetime

from app.modules.audit_logs.model import AuditAction
from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.audit_logs.schema import AuditLogRead
from app.modules.users.model import User


class AuditLogService:
    def __init__(self, repository: AuditLogRepository) -> None:
        self.repository = repository

    def log_user_created(self, user: User, performed_by: User) -> None:
        self.repository.create(
            action=AuditAction.USER_CREATED,
            performed_by_id=performed_by.id,
            performed_by_name=performed_by.name,
            target_user_id=user.id,
            target_user_name=user.name,
            target_user_email=user.email,
            target_user_role=user.role.value,
        )

    def log_user_deactivated(self, user: User, performed_by: User) -> None:
        self.repository.create(
            action=AuditAction.USER_DEACTIVATED,
            performed_by_id=performed_by.id,
            performed_by_name=performed_by.name,
            target_user_id=user.id,
            target_user_name=user.name,
            target_user_email=user.email,
            target_user_role=user.role.value,
        )

    def list_logs(
        self,
        action: AuditAction | None,
        date_from: datetime | None,
        date_to: datetime | None,
        page: int,
        limit: int,
    ) -> tuple[list[AuditLogRead], int]:
        logs, total = self.repository.get_all(
            action=action, date_from=date_from, date_to=date_to, page=page, limit=limit
        )
        return [AuditLogRead.model_validate(log) for log in logs], total
