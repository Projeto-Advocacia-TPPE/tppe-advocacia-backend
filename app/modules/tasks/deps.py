from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.clients.repository import ClientRepository
from app.modules.notifications.deps import get_notification_service
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.service import TaskService
from app.modules.users.repository import UserRepository


def get_task_service(
    db: Session = Depends(get_db),
    notifications: NotificationService = Depends(get_notification_service),
) -> TaskService:
    return TaskService(
        TaskRepository(db),
        ClientRepository(db),
        ProcessRepository(db),
        UserRepository(db),
        notifications,
    )
