from sqlalchemy.orm import Session

from app.modules.datajud.protocol import DataJudClient
from app.modules.datajud.schema import (
    DataJudBatchSyncRequest,
    DataJudBatchSyncResponse,
    DataJudSyncRequest,
    DataJudSyncResponse,
)
from app.modules.datajud.service import DataJudService
from app.modules.email.protocol import EmailService
from app.modules.external_api_logs.notifier import ExternalApiFailureNotifier
from app.modules.external_api_logs.repository import ExternalApiLogRepository
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.users.repository import UserRepository


class DataJudController:
    def __init__(
        self,
        db: Session,
        datajud_client: DataJudClient,
        email: EmailService,
    ) -> None:
        users = UserRepository(db)
        notifications = NotificationService(
            NotificationPreferenceRepository(db),
            users,
            email,
        )
        self.service = DataJudService(
            ProcessRepository(db),
            ExternalApiLogRepository(db),
            datajud_client,
            failure_notifier=ExternalApiFailureNotifier(users, notifications),
        )

    def sync_process_movements(
        self,
        process_id: int,
        payload: DataJudSyncRequest,
        actor_id: int | None,
    ) -> DataJudSyncResponse:
        return self.service.sync_process_movements(
            process_id=process_id,
            payload=payload,
            actor_id=actor_id,
        )

    def sync_active_processes(
        self,
        payload: DataJudBatchSyncRequest,
        actor_id: int | None,
    ) -> DataJudBatchSyncResponse:
        return self.service.sync_active_processes(
            payload=payload,
            actor_id=actor_id,
        )
