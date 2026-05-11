from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.audit_logs.model import AuditAction
from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.audit_logs.schema import AuditLogRead
from app.modules.audit_logs.service import AuditLogService


class AuditLogController:
    def __init__(self, db: Session) -> None:
        self.service = AuditLogService(AuditLogRepository(db))

    def list_logs(
        self,
        action: AuditAction | None,
        date_from: datetime | None,
        date_to: datetime | None,
        page: int,
        limit: int,
    ) -> tuple[list[AuditLogRead], int]:
        return self.service.list_logs(
            action=action, date_from=date_from, date_to=date_to, page=page, limit=limit
        )
