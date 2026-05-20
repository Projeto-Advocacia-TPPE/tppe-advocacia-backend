from datetime import datetime

from app.modules.external_api_logs.model import (
    ExternalApiLog,
    ExternalApiProvider,
    ExternalApiStatus,
)
from app.modules.external_api_logs.repository import ExternalApiLogRepository


class ExternalApiLogService:
    def __init__(self, repository: ExternalApiLogRepository) -> None:
        self.repository = repository

    def list_logs(
        self,
        provider: ExternalApiProvider | None = None,
        status: ExternalApiStatus | None = None,
        process_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ExternalApiLog], int]:
        return self.repository.list(
            provider=provider,
            status=status,
            process_id=process_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
        )
