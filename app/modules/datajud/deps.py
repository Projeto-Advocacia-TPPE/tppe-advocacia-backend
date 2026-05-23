from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.datajud.datajud_service import DataJudApiService
from app.modules.datajud.protocol import DataJudClient
from app.modules.datajud.service import DataJudService
from app.modules.email.protocol import EmailService
from app.modules.external_api_logs.notifier import ExternalApiFailureNotifier
from app.modules.external_api_logs.repository import ExternalApiLogRepository
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.users.repository import UserRepository
from app.shared.email_deps import get_email_service


def get_datajud_client() -> DataJudClient:
    return DataJudApiService()


def get_datajud_service(
    db: Session = Depends(get_db),
    datajud_client: DataJudClient = Depends(get_datajud_client),
    email: EmailService = Depends(get_email_service),
) -> DataJudService:
    users = UserRepository(db)
    notifications = NotificationService(
        NotificationPreferenceRepository(db),
        users,
        email,
    )
    return DataJudService(
        ProcessRepository(db),
        ExternalApiLogRepository(db),
        datajud_client,
        failure_notifier=ExternalApiFailureNotifier(users, notifications),
    )
