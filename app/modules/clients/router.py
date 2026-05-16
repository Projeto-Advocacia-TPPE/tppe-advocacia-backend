from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.clients.controller import ClientController
from app.modules.clients.schema import (
    ClientCreate,
    ClientListItem,
    ClientRead,
    ClientUpdate,
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

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post(
    "",
    response_model=SuccessResponse[ClientRead],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401, 409, 422),
    summary="Cria um novo cliente",
)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[ClientRead]:
    return ok(ClientController(db).create_client(payload, created_by=current_user))


@router.get(
    "",
    response_model=PaginatedResponse[ClientListItem],
    responses=error_responses(401),
    summary="Lista clientes com paginação e busca opcional",
)
def list_clients(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[ClientListItem]:
    items, total = ClientController(db).list_clients(
        search=search, page=page, limit=limit
    )
    return paginated(items, total=total, page=page, limit=limit)


@router.get(
    "/{client_id}",
    response_model=SuccessResponse[ClientRead],
    responses=error_responses(401, 404),
    summary="Retorna dados de um cliente",
)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SuccessResponse[ClientRead]:
    return ok(ClientController(db).get_client(client_id))


@router.patch(
    "/{client_id}",
    response_model=SuccessResponse[ClientRead],
    responses=error_responses(401, 404, 409, 422),
    summary="Atualiza parcialmente um cliente",
)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[ClientRead]:
    return ok(
        ClientController(db).update_client(client_id, payload, updated_by=current_user)
    )
