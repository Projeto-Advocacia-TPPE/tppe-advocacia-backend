from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.forensic_holidays.repository import ForensicHolidayRepository
from app.modules.forensic_holidays.schema import (
    HolidayCreate,
    HolidayRead,
    HolidayUpdate,
)
from app.modules.forensic_holidays.service import ForensicHolidayService


class ForensicHolidayController:
    def __init__(self, db: Session) -> None:
        self.service = ForensicHolidayService(ForensicHolidayRepository(db))

    def create(self, payload: HolidayCreate) -> HolidayRead:
        return HolidayRead.model_validate(self.service.create(payload))

    def get(self, holiday_id: int) -> HolidayRead:
        return HolidayRead.model_validate(self.service.get(holiday_id))

    def list(
        self,
        year: int | None,
        court: str | None,
        comarca: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[HolidayRead], int]:
        items, total = self.service.list(year, court, comarca, page=page, limit=limit)
        return [HolidayRead.model_validate(h) for h in items], total

    def update(self, holiday_id: int, payload: HolidayUpdate) -> HolidayRead:
        return HolidayRead.model_validate(self.service.update(holiday_id, payload))

    def delete(self, holiday_id: int) -> None:
        self.service.delete(holiday_id)
