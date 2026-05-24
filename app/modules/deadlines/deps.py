from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.deadlines.repository import DeadlineAlertRepository, DeadlineRepository
from app.modules.deadlines.service import DeadlineService
from app.modules.forensic_holidays.repository import ForensicHolidayRepository
from app.modules.notifications.deps import get_notification_service
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository


def get_deadline_service(
    db: Session = Depends(get_db),
    notifications: NotificationService = Depends(get_notification_service),
) -> DeadlineService:
    return DeadlineService(
        DeadlineRepository(db),
        ForensicHolidayRepository(db),
        ProcessRepository(db),
        alert_repository=DeadlineAlertRepository(db),
        notification_service=notifications,
    )
