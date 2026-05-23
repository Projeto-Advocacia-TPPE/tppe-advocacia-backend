from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.clients.repository import ClientRepository
from app.modules.email.protocol import EmailService
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.service import ProcessService
from app.modules.users.repository import UserRepository
from app.shared.email_deps import get_email_service


def get_process_service(
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
) -> ProcessService:
    users_repo = UserRepository(db)
    return ProcessService(
        ProcessRepository(db),
        ClientRepository(db),
        notifications=NotificationService(
            NotificationPreferenceRepository(db),
            users_repo,
            email,
        ),
    )
