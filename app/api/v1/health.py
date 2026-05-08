from fastapi import APIRouter

from app.controllers.health_controller import HealthController
from app.schemas.health import HealthResponse
from app.utils.responses import SuccessResponse, ok

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=SuccessResponse[HealthResponse],
    summary="Verifica a saúde da API",
)
def read_health() -> SuccessResponse[HealthResponse]:
    return ok(HealthController().get_status())
