from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.modules.audit_logs.deps import get_audit_log_service
from app.modules.audit_logs.model import AuditAction
from app.modules.audit_logs.schema import AuditLogRead
from app.modules.audit_logs.service import AuditLogService
from app.modules.users.model import User
from app.shared.auth_deps import require_admin
from app.shared.responses import PaginatedResponse, error_responses, paginated

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogRead],
    responses=error_responses(401, 403),
    summary="List audit logs for user operations",
)
def list_audit_logs(
    action: AuditAction | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: AuditLogService = Depends(get_audit_log_service),
    _: User = Depends(require_admin),
) -> PaginatedResponse[AuditLogRead]:
    items, total = service.list_logs(
        action=action, date_from=date_from, date_to=date_to, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)
