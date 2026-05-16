from app.modules.leads.model import Lead
from app.modules.leads.repository import LeadRepository
from app.modules.leads.schema import LeadCreate


class LeadService:
    def __init__(self, repository: LeadRepository) -> None:
        self.repository = repository

    def list_leads(self) -> list[Lead]:
        return self.repository.get_all()

    def create_lead(self, payload: LeadCreate) -> Lead:
        return self.repository.create(payload)
