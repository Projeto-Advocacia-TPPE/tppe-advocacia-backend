from __future__ import annotations

from app.modules.forensic_holidays.model import ForensicHoliday, HolidayScope
from app.modules.forensic_holidays.repository import ForensicHolidayRepository
from app.modules.forensic_holidays.schema import (
    HolidayCreate,
    HolidayUpdate,
    _validate_scope_consistency,
)
from app.shared.exceptions import ForensicHolidayNotFoundError


class ForensicHolidayService:
    def __init__(self, repository: ForensicHolidayRepository) -> None:
        self.repository = repository

    def create(self, payload: HolidayCreate) -> ForensicHoliday:
        return self.repository.create(
            date_=payload.date,
            description=payload.description,
            scope=payload.scope,
            court=payload.court,
            comarca=payload.comarca,
        )

    def get(self, holiday_id: int) -> ForensicHoliday:
        holiday = self.repository.get_by_id(holiday_id)
        if holiday is None:
            raise ForensicHolidayNotFoundError()
        return holiday

    def list(
        self,
        year: int | None,
        court: str | None,
        comarca: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[ForensicHoliday], int]:
        return self.repository.list(year, court, comarca, page=page, limit=limit)

    def update(self, holiday_id: int, payload: HolidayUpdate) -> ForensicHoliday:
        holiday = self.get(holiday_id)

        fields = payload.model_dump(exclude_unset=True)
        new_scope: HolidayScope = fields.get("scope", holiday.scope)
        new_court = fields["court"] if "court" in fields else holiday.court
        new_comarca = fields["comarca"] if "comarca" in fields else holiday.comarca

        _validate_scope_consistency(new_scope, new_court, new_comarca)

        return self.repository.update(
            holiday,
            date_=fields.get("date"),
            description=fields.get("description"),
            scope=fields.get("scope"),
            court=fields.get("court") if fields.get("court") is not None else None,
            comarca=fields.get("comarca")
            if fields.get("comarca") is not None
            else None,
            clear_court="court" in fields and fields["court"] is None,
            clear_comarca="comarca" in fields and fields["comarca"] is None,
        )

    def delete(self, holiday_id: int) -> None:
        holiday = self.get(holiday_id)
        self.repository.delete(holiday)
