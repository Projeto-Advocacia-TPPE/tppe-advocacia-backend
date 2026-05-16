from sqlalchemy.orm import Session

from app.modules.leads.model import Lead
from app.modules.leads.repository import LeadRepository
from app.modules.leads.schema import LeadCreate
from app.modules.leads.service import LeadService


class LeadController:
    def __init__(self, db: Session) -> None:
        self.service = LeadService(LeadRepository(db))

    def list_leads(self) -> list[Lead]:
        return self.service.list_leads()

    def create_lead(self, payload: LeadCreate) -> Lead:
        return self.service.create_lead(payload)
