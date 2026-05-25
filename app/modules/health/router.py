from fastapi import APIRouter, Depends

from app.modules.health.deps import get_health_service
from app.modules.health.schema import HealthResponse
from app.modules.health.service import HealthService
from app.shared.http.responses import SuccessResponse, ok

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=SuccessResponse[HealthResponse],
    summary="Verifica a saúde da API",
)
def read_health(
    service: HealthService = Depends(get_health_service),
) -> SuccessResponse[HealthResponse]:
    return ok(service.get_status())
