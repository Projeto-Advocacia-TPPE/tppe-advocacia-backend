from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.leads.repository import LeadRepository
from app.modules.leads.service import LeadService
from app.modules.notifications.deps import get_notification_service
from app.modules.notifications.service import NotificationService
from app.modules.users.repository import UserRepository


def get_lead_service(
    db: Session = Depends(get_db),
    notifications: NotificationService = Depends(get_notification_service),
) -> LeadService:
    return LeadService(
        LeadRepository(db),
        UserRepository(db),
        notifications=notifications,
    )
