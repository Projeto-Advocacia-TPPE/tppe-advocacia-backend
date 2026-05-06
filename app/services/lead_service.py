from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate


class LeadService:
    def __init__(self, db: Session) -> None:
        self.repository = LeadRepository(db)

    def list_leads(self) -> list[Lead]:
        return self.repository.get_all()

    def create_lead(self, payload: LeadCreate) -> Lead:
        return self.repository.create(payload)
