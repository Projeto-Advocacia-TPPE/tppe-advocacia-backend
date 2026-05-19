from sqlalchemy.orm import Session

from app.modules.email.protocol import EmailService
from app.modules.leads.model import Lead, LeadStatus
from app.modules.leads.repository import LeadRepository
from app.modules.leads.schema import LeadCreate, LeadUpdate
from app.modules.leads.service import LeadService
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.service import NotificationService
from app.modules.users.model import User
from app.modules.users.repository import UserRepository


class LeadController:
    def __init__(self, db: Session, email: EmailService | None = None) -> None:
        users_repo = UserRepository(db)
        notifications = (
            NotificationService(NotificationPreferenceRepository(db), users_repo, email)
            if email is not None
            else None
        )
        self.service = LeadService(
            LeadRepository(db), users_repo, notifications=notifications
        )

    def list_leads(
        self,
        status: LeadStatus | None = None,
        assigned_to: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Lead], int]:
        return self.service.list_leads(
            status=status, assigned_to=assigned_to, page=page, limit=limit
        )

    def create_lead(self, payload: LeadCreate) -> Lead:
        return self.service.create_lead(payload)

    def update_lead(
        self, lead_id: int, payload: LeadUpdate, current_user: User | None = None
    ) -> Lead:
        return self.service.update_lead(lead_id, payload, current_user=current_user)
