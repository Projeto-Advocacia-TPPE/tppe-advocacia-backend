from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.email.protocol import EmailService
from app.modules.leads.controller import LeadController
from app.modules.leads.model import LeadStatus
from app.modules.leads.schema import LeadCreate, LeadRead, LeadUpdate
from app.modules.users.model import User
from app.shared.auth_deps import require_admin
from app.shared.email_deps import get_email_service
from app.shared.responses import (
    PaginatedResponse,
    SuccessResponse,
    error_responses,
    ok,
    paginated,
)

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get(
    "",
    response_model=PaginatedResponse[LeadRead],
    responses=error_responses(401, 403),
    summary="Lista os leads cadastrados (admin)",
)
def read_leads(
    status: LeadStatus | None = Query(None),
    assigned_to: int | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> PaginatedResponse[LeadRead]:
    items, total = LeadController(db).list_leads(
        status=status, assigned_to=assigned_to, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)


@router.post(
    "",
    response_model=SuccessResponse[LeadRead],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409, 422),
    summary="Cria um novo lead (público)",
)
def create_new_lead(
    payload: LeadCreate, db: Session = Depends(get_db)
) -> SuccessResponse[LeadRead]:
    return ok(LeadController(db).create_lead(payload))


@router.patch(
    "/{lead_id}",
    response_model=SuccessResponse[LeadRead],
    responses=error_responses(401, 403, 404, 422),
    summary="Atualiza status ou responsável do lead (admin). Retorna 422 se assigned_to não existir.",
)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse[LeadRead]:
    return ok(
        LeadController(db, email).update_lead(
            lead_id, payload, current_user=current_user
        )
    )
