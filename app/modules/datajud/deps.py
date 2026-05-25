from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.datajud.datajud_service import DataJudApiService
from app.modules.datajud.protocol import DataJudClient
from app.modules.datajud.service import DataJudService
from app.modules.external_api_logs.notifier import ExternalApiFailureNotifier
from app.modules.external_api_logs.repository import ExternalApiLogRepository
from app.modules.notifications.deps import get_notification_service
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.users.repository import UserRepository


@lru_cache(maxsize=1)
def get_datajud_client() -> DataJudClient:
    return DataJudApiService()


def get_datajud_service(
    db: Session = Depends(get_db),
    datajud_client: DataJudClient = Depends(get_datajud_client),
    notifications: NotificationService = Depends(get_notification_service),
) -> DataJudService:
    return DataJudService(
        ProcessRepository(db),
        ExternalApiLogRepository(db),
        datajud_client,
        failure_notifier=ExternalApiFailureNotifier(
            UserRepository(db),
            notifications,
            ExternalApiLogRepository(db),
        ),
    )
