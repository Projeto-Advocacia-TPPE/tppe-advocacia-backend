from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.email.protocol import EmailService
from app.modules.leads.repository import LeadRepository
from app.modules.leads.service import LeadService
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.service import NotificationService
from app.modules.users.repository import UserRepository
from app.shared.email_deps import get_email_service


def get_lead_service(
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
) -> LeadService:
    users_repo = UserRepository(db)
    return LeadService(
        LeadRepository(db),
        users_repo,
        notifications=NotificationService(
            NotificationPreferenceRepository(db),
            users_repo,
            email,
        ),
    )
