from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.clients.repository import ClientRepository
from app.modules.notifications.deps import get_notification_service
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.service import ProcessService


def get_process_service(
    db: Session = Depends(get_db),
    notifications: NotificationService = Depends(get_notification_service),
) -> ProcessService:
    return ProcessService(
        ProcessRepository(db),
        ClientRepository(db),
        notifications=notifications,
    )
