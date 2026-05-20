"""Jobs executados pelo scheduler.

Cada job abre sua própria Session (fora do ciclo de request) e monta o
grafo de dependências necessário, seguindo o mesmo padrão de injeção
manual usado pelos controllers.
"""

import logging
from datetime import date

from app.config.settings import get_settings
from app.db.database import SessionLocal
from app.modules.deadlines.repository import (
    DeadlineAlertRepository,
    DeadlineRepository,
)
from app.modules.deadlines.service import DeadlineService
from app.modules.email.resend_service import ResendEmailService
from app.modules.forensic_holidays.repository import ForensicHolidayRepository
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.users.repository import UserRepository

logger = logging.getLogger(__name__)


def dispatch_deadline_alerts_job() -> None:
    """Varre os prazos e dispara os alertas escalonados pendentes (US-28)."""
    logger.info("Deadline alerts job started")
    try:
        settings = get_settings()
        with SessionLocal() as db:
            notification_service = NotificationService(
                NotificationPreferenceRepository(db),
                UserRepository(db),
                ResendEmailService(),
            )
            service = DeadlineService(
                repository=DeadlineRepository(db),
                holiday_repository=ForensicHolidayRepository(db),
                process_repository=ProcessRepository(db),
                alert_repository=DeadlineAlertRepository(db),
                notification_service=notification_service,
                alert_intervals=settings.deadline_alert_intervals,
            )
            sent = service.dispatch_alerts(today=date.today())
        logger.info("Deadline alerts job finished — %d alert(s) sent", sent)
    except Exception:
        logger.exception("Deadline alerts job failed")
