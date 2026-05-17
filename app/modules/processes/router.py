from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.processes.controller import ProcessController
from app.modules.processes.model import ProcessStatus
from app.modules.processes.schema import (
    ProcessCreate,
    ProcessListItem,
    ProcessRead,
)
from app.modules.users.model import User
from app.shared.auth_deps import get_current_user
from app.shared.responses import (
    PaginatedResponse,
    SuccessResponse,
    error_responses,
    ok,
    paginated,
)

router = APIRouter(tags=["Processes"])


@router.post(
    "/processes",
    response_model=SuccessResponse[ProcessRead],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401, 409, 422),
    summary="Cria um novo processo judicial",
)
def create_process(
    payload: ProcessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[ProcessRead]:
    return ok(ProcessController(db).create_process(payload, created_by=current_user))


@router.get(
    "/processes",
    response_model=PaginatedResponse[ProcessListItem],
    responses=error_responses(401),
    summary="Lista processos com filtros e paginação",
)
def list_processes(
    client_id: int | None = Query(None),
    status_filter: ProcessStatus | None = Query(None, alias="status"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[ProcessListItem]:
    items, total = ProcessController(db).list_processes(
        client_id=client_id,
        status=status_filter,
        search=search,
        page=page,
        limit=limit,
    )
    return paginated(items, total=total, page=page, limit=limit)


@router.get(
    "/processes/{process_id}",
    response_model=SuccessResponse[ProcessRead],
    responses=error_responses(401, 404),
    summary="Retorna dados de um processo",
)
def get_process(
    process_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SuccessResponse[ProcessRead]:
    return ok(ProcessController(db).get_process(process_id))


@router.get(
    "/clients/{client_id}/processes",
    response_model=PaginatedResponse[ProcessListItem],
    responses=error_responses(401, 404),
    summary="Lista processos de um cliente específico",
)
def list_processes_by_client(
    client_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[ProcessListItem]:
    items, total = ProcessController(db).list_by_client(
        client_id, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)
