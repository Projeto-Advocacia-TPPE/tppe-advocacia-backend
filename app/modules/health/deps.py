from app.modules.health.service import HealthService


def get_health_service() -> HealthService:
    return HealthService()
