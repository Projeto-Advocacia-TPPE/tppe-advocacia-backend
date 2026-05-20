from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.deadlines.repository import DeadlineRepository
from app.modules.deadlines.schema import (
    DeadlineCalculateRequest,
    DeadlineCalculateResponse,
    DeadlineCreate,
    DeadlineRead,
    DeadlineUpdate,
)
from app.modules.deadlines.service import DeadlineService
from app.modules.forensic_holidays.repository import ForensicHolidayRepository
from app.modules.processes.repository import ProcessRepository
from app.modules.users.model import User


class DeadlineController:
    def __init__(self, db: Session) -> None:
        self.service = DeadlineService(
            DeadlineRepository(db),
            ForensicHolidayRepository(db),
            ProcessRepository(db),
        )

    def calculate(self, payload: DeadlineCalculateRequest) -> DeadlineCalculateResponse:
        due_date, skipped = self.service.calculate_due_date(
            start_date=payload.start_date,
            business_days=payload.business_days,
            court=payload.court,
            comarca=payload.comarca,
        )
        return DeadlineCalculateResponse(
            start_date=payload.start_date,
            business_days=payload.business_days,
            due_date=due_date,
            court=payload.court,
            comarca=payload.comarca,
            skipped_days=skipped,
        )

    def create_for_process(
        self, process_id: int, payload: DeadlineCreate, current_user: User
    ) -> DeadlineRead:
        deadline = self.service.create_for_process(
            process_id, payload, created_by_id=current_user.id
        )
        return DeadlineRead.model_validate(deadline)

    def list_by_process(
        self, process_id: int, page: int, limit: int
    ) -> tuple[list[DeadlineRead], int]:
        items, total = self.service.list_by_process(process_id, page=page, limit=limit)
        return [DeadlineRead.model_validate(d) for d in items], total

    def update(self, deadline_id: int, payload: DeadlineUpdate) -> DeadlineRead:
        return DeadlineRead.model_validate(self.service.update(deadline_id, payload))

    def delete(self, deadline_id: int) -> None:
        self.service.delete(deadline_id)
