from fastapi import APIRouter

from app.controllers.health_controller import HealthController
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse, summary="Verifica a saúde da API")
def read_health() -> HealthResponse:
    return HealthController().get_status()
