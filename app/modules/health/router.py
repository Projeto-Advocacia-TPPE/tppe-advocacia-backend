from fastapi import APIRouter

from app.modules.health.controller import HealthController
from app.modules.health.schema import HealthResponse
from app.shared.responses import SuccessResponse, ok

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=SuccessResponse[HealthResponse],
    summary="Verifica a saúde da API",
)
def read_health() -> SuccessResponse[HealthResponse]:
    return ok(HealthController().get_status())
