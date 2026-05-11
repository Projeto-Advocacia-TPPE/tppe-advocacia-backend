from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.audit_logs.model import AuditAction


class AuditLogRead(BaseModel):
    id: int
    action: AuditAction
    performed_by_id: int | None
    performed_by_name: str | None
    target_user_id: int
    target_user_name: str
    target_user_email: str
    target_user_role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
