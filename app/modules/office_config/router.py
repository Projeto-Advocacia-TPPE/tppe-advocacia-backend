from fastapi import APIRouter, Depends

from app.modules.office_config.deps import get_office_config_service
from app.modules.office_config.schema import OfficeConfigRead, OfficeConfigUpdate
from app.modules.office_config.service import OfficeConfigService
from app.modules.users.model import User
from app.shared.deps.auth import require_admin
from app.shared.http.responses import SuccessResponse, error_responses, ok

router = APIRouter(prefix="/office-config", tags=["Office Config"])


@router.get(
    "",
    response_model=SuccessResponse[OfficeConfigRead],
    summary="Retorna a configuração atual do escritório",
)
def get_office_config(
    service: OfficeConfigService = Depends(get_office_config_service),
) -> SuccessResponse[OfficeConfigRead]:
    return ok(OfficeConfigRead.model_validate(service.get()))


@router.patch(
    "",
    response_model=SuccessResponse[OfficeConfigRead],
    responses=error_responses(401, 403),
    summary="Atualiza a configuração do escritório (admin only)",
)
def update_office_config(
    payload: OfficeConfigUpdate,
    service: OfficeConfigService = Depends(get_office_config_service),
    _: User = Depends(require_admin),
) -> SuccessResponse[OfficeConfigRead]:
    return ok(OfficeConfigRead.model_validate(service.update(payload)))
