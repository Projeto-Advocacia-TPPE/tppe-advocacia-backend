from sqlalchemy.orm import Session

from app.modules.leads.model import Lead, LeadStatus
from app.modules.leads.repository import LeadRepository
from app.modules.leads.schema import LeadCreate, LeadUpdate
from app.modules.leads.service import LeadService


class LeadController:
    def __init__(self, db: Session) -> None:
        self.service = LeadService(LeadRepository(db))

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

    def update_lead(self, lead_id: int, payload: LeadUpdate) -> Lead:
        return self.service.update_lead(lead_id, payload)
