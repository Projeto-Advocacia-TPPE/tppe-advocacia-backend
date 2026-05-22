from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.external_api_logs.controller import ExternalApiLogController
from app.modules.external_api_logs.model import ExternalApiProvider, ExternalApiStatus
from app.modules.external_api_logs.schema import ExternalApiLogRead
from app.modules.users.model import User
from app.shared.auth_deps import require_admin
from app.shared.responses import PaginatedResponse, error_responses, paginated

router = APIRouter(prefix="/external-api-logs", tags=["External API Logs"])


@router.get(
    "",
    response_model=PaginatedResponse[ExternalApiLogRead],
    responses=error_responses(401, 403),
    summary="Lista logs de chamadas a APIs externas",
)
def list_external_api_logs(
    provider: ExternalApiProvider | None = Query(None),
    status: ExternalApiStatus | None = Query(None),
    process_id: int | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> PaginatedResponse[ExternalApiLogRead]:
    items, total = ExternalApiLogController(db).list_logs(
        provider=provider,
        status=status,
        process_id=process_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )
    return paginated(items, total=total, page=page, limit=limit)
