from app.config.settings import get_settings
from app.modules.leads.model import Lead, LeadStatus
from app.modules.leads.repository import LeadRepository
from app.modules.leads.schema import LeadCreate, LeadUpdate
from app.modules.notifications.schema import EventType
from app.modules.notifications.service import NotificationService
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.shared.exceptions import (
    AssigneeNotFoundError,
    LeadDuplicateError,
    LeadNotFoundError,
)
from app.shared.uow import unit_of_work

settings = get_settings()


class LeadService:
    def __init__(
        self,
        repository: LeadRepository,
        user_repository: UserRepository,
        notifications: NotificationService | None = None,
    ) -> None:
        self.repository = repository
        self.user_repository = user_repository
        self.notifications = notifications

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
        with unit_of_work(self.repository.db):
            lead = self.repository.create(
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                message=payload.message,
            )
        return lead

    def update_lead(
        self, lead_id: int, payload: LeadUpdate, current_user: User | None = None
    ) -> Lead:
        lead = self.get_lead(lead_id)
        data = payload.model_dump(exclude_none=True)
        if not data:
            return lead
        if (
            "assigned_to" in data
            and self.user_repository.get_by_id(data["assigned_to"]) is None
        ):
            raise AssigneeNotFoundError()

        previous_assignee = lead.assigned_to
        with unit_of_work(self.repository.db):
            updated = self.repository.update(lead, data)

        new_assignee = data.get("assigned_to")
        actor_id = current_user.id if current_user is not None else None
        if (
            "assigned_to" in data
            and new_assignee is not None
            and new_assignee != previous_assignee
            and new_assignee != actor_id
        ):
            self._notify_assignee(updated)

        return updated

    def _notify_assignee(self, lead: Lead) -> None:
        if self.notifications is None:
            return
        self.notifications.notify(
            user_id=lead.assigned_to,
            event_type=EventType.LEAD_ASSIGNED,
            payload={
                "lead_id": lead.id,
                "lead_name": lead.name,
                "lead_email": lead.email,
                "lead_phone": lead.phone,
            },
        )
