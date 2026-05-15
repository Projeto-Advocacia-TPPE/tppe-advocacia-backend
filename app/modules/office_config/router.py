from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.office_config.controller import OfficeConfigController
from app.modules.office_config.schema import OfficeConfigRead, OfficeConfigUpdate
from app.modules.users.model import User
from app.shared.auth_deps import require_admin
from app.shared.responses import SuccessResponse, error_responses, ok

router = APIRouter(prefix="/office-config", tags=["Office Config"])


@router.get(
    "",
    response_model=SuccessResponse[OfficeConfigRead],
    summary="Retorna a configuração atual do escritório",
)
def get_office_config(
    db: Session = Depends(get_db),
) -> SuccessResponse[OfficeConfigRead]:
    return ok(OfficeConfigController(db).get())


@router.patch(
    "",
    response_model=SuccessResponse[OfficeConfigRead],
    responses=error_responses(401, 403),
    summary="Atualiza a configuração do escritório (admin only)",
)
def update_office_config(
    payload: OfficeConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SuccessResponse[OfficeConfigRead]:
    return ok(OfficeConfigController(db).update(payload))
