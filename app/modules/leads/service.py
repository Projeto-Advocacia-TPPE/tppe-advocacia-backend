from app.config.settings import get_settings
from app.modules.leads.model import Lead, LeadStatus
from app.modules.leads.repository import LeadRepository
from app.modules.leads.schema import LeadCreate, LeadUpdate
from app.shared.exceptions import LeadDuplicateError, LeadNotFoundError

settings = get_settings()


class LeadService:
    def __init__(self, repository: LeadRepository) -> None:
        self.repository = repository

    def list_leads(
        self,
        status: LeadStatus | None = None,
        assigned_to: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Lead], int]:
        return self.repository.get_all(
            status=status, assigned_to=assigned_to, page=page, limit=limit
        )

    def get_lead(self, lead_id: int) -> Lead:
        lead = self.repository.get_by_id(lead_id)
        if lead is None:
            raise LeadNotFoundError()
        return lead

    def create_lead(self, payload: LeadCreate) -> Lead:
        if self.repository.find_recent_by_email(
            payload.email, settings.lead_dedup_window_hours
        ):
            raise LeadDuplicateError()
        return self.repository.create(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            message=payload.message,
        )

    def update_lead(self, lead_id: int, payload: LeadUpdate) -> Lead:
        lead = self.get_lead(lead_id)
        data = payload.model_dump(exclude_none=True)
        if not data:
            return lead
        return self.repository.update(lead, data)
