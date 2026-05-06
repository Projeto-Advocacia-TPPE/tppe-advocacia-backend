from app.config.settings import get_settings
from app.db.database import check_database_connection
from app.schemas.health import HealthResponse


class HealthController:
    def get_status(self) -> HealthResponse:
        settings = get_settings()
        database_status = "connected" if check_database_connection() else "unavailable"
        overall_status = "ok" if database_status == "connected" else "degraded"

        return HealthResponse(
            status=overall_status,
            app_name=settings.app_name,
            version=settings.app_version,
            database=database_status,
        )
