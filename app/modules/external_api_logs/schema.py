from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.external_api_logs.model import (
    ExternalApiOperation,
    ExternalApiProvider,
    ExternalApiStatus,
)


class ExternalApiLogRead(BaseModel):
    id: int
    provider: ExternalApiProvider
    operation: ExternalApiOperation
    status: ExternalApiStatus
    process_id: int | None
    tribunal_alias: str | None
    request_identifier: str | None
    http_status: int | None
    error_code: str | None
    error_message: str | None
    created_by: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
