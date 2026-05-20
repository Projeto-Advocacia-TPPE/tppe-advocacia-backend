from __future__ import annotations

from datetime import date, timedelta

from app.modules.deadlines.model import Deadline
from app.modules.deadlines.repository import DeadlineRepository
from app.modules.deadlines.schema import (
    DeadlineCreate,
    DeadlineUpdate,
    SkippedDay,
    SkipReason,
)
from app.modules.forensic_holidays.model import ForensicHoliday
from app.modules.forensic_holidays.repository import ForensicHolidayRepository
from app.modules.processes.repository import ProcessRepository
from app.shared.exceptions import (
    DeadlineNotFoundError,
    InvalidDeadlineRangeError,
    ProcessNotFoundError,
)


class DeadlineService:
    def __init__(
        self,
        repository: DeadlineRepository,
        holiday_repository: ForensicHolidayRepository,
        process_repository: ProcessRepository,
    ) -> None:
        self.repository = repository
        self.holiday_repository = holiday_repository
        self.process_repository = process_repository

    def calculate_due_date(
        self,
        start_date: date,
        business_days: int,
        court: str | None,
        comarca: str | None,
    ) -> tuple[date, list[SkippedDay]]:
        if business_days <= 0:
            raise InvalidDeadlineRangeError()

        end_horizon = start_date + timedelta(days=business_days * 3 + 60)
        holidays = self.holiday_repository.list_applicable_in_range(
            start=start_date,
            end=end_horizon,
            court=court,
            comarca=comarca,
        )
        holiday_map: dict[date, ForensicHoliday] = {h.date: h for h in holidays}

        skipped: list[SkippedDay] = []

        current = start_date
        while not _is_business_day(current, holiday_map):
            skipped.append(_skip_for(current, holiday_map))
            current += timedelta(days=1)

        counted = 0
        while counted < business_days:
            current += timedelta(days=1)
            while not _is_business_day(current, holiday_map):
                skipped.append(_skip_for(current, holiday_map))
                current += timedelta(days=1)
            counted += 1

        return current, skipped

    def create_for_process(
        self,
        process_id: int,
        payload: DeadlineCreate,
        created_by_id: int | None,
    ) -> Deadline:
        process = self.process_repository.get_by_id(process_id)
        if process is None:
            raise ProcessNotFoundError()

        court = process.court
        comarca = payload.comarca

        due_date, _ = self.calculate_due_date(
            start_date=payload.start_date,
            business_days=payload.business_days,
            court=court,
            comarca=comarca,
        )

        return self.repository.create(
            process_id=process_id,
            start_date=payload.start_date,
            business_days=payload.business_days,
            deadline_type=payload.deadline_type,
            due_date=due_date,
            court=court,
            comarca=comarca,
            created_by=created_by_id,
        )

    def list_by_process(
        self, process_id: int, page: int, limit: int
    ) -> tuple[list[Deadline], int]:
        process = self.process_repository.get_by_id(process_id)
        if process is None:
            raise ProcessNotFoundError()
        return self.repository.list_by_process(process_id, page=page, limit=limit)

    def update(self, deadline_id: int, payload: DeadlineUpdate) -> Deadline:
        deadline = self.repository.get_by_id(deadline_id)
        if deadline is None:
            raise DeadlineNotFoundError()

        fields = payload.model_dump(exclude_unset=True)

        new_start = fields.get("start_date", deadline.start_date)
        new_days = fields.get("business_days", deadline.business_days)
        comarca_changed = "comarca" in fields
        new_comarca = fields["comarca"] if comarca_changed else deadline.comarca

        recalc_needed = (
            "start_date" in fields or "business_days" in fields or comarca_changed
        )

        new_due_date = None
        if recalc_needed:
            new_due_date, _ = self.calculate_due_date(
                start_date=new_start,
                business_days=new_days,
                court=deadline.court,
                comarca=new_comarca,
            )

        return self.repository.update(
            deadline,
            start_date=fields.get("start_date"),
            business_days=fields.get("business_days"),
            deadline_type=fields.get("deadline_type"),
            comarca=fields.get("comarca")
            if comarca_changed and fields["comarca"] is not None
            else None,
            due_date=new_due_date,
            clear_comarca=comarca_changed and fields["comarca"] is None,
        )

    def delete(self, deadline_id: int) -> None:
        deadline = self.repository.get_by_id(deadline_id)
        if deadline is None:
            raise DeadlineNotFoundError()
        self.repository.delete(deadline)


def _is_business_day(d: date, holiday_map: dict[date, ForensicHoliday]) -> bool:
    if d.weekday() >= 5:
        return False
    if d in holiday_map:
        return False
    return True


def _skip_for(d: date, holiday_map: dict[date, ForensicHoliday]) -> SkippedDay:
    if d in holiday_map:
        return SkippedDay(
            date=d,
            reason=SkipReason.HOLIDAY,
            description=holiday_map[d].description,
        )
    return SkippedDay(date=d, reason=SkipReason.WEEKEND, description=None)
