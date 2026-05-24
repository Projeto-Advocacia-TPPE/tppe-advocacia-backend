from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.external_api_logs.repository import ExternalApiLogRepository
from app.modules.external_api_logs.service import ExternalApiLogService


def get_external_api_log_service(
    db: Session = Depends(get_db),
) -> ExternalApiLogService:
    return ExternalApiLogService(ExternalApiLogRepository(db))
