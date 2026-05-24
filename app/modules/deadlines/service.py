from __future__ import annotations

import logging
from datetime import date, timedelta

from app.modules.deadlines.model import Deadline, DeadlineAlert
from app.modules.deadlines.repository import (
    DeadlineAlertRepository,
    DeadlineRepository,
)
from app.modules.deadlines.schema import (
    DeadlineCreate,
    DeadlineUpdate,
    SkippedDay,
    SkipReason,
)
from app.modules.forensic_holidays.model import ForensicHoliday
from app.modules.forensic_holidays.repository import ForensicHolidayRepository
from app.modules.notifications.schema import EventType
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.schema import format_cnj
from app.modules.users.model import User
from app.shared.exceptions import (
    DeadlineNotFoundError,
    InvalidDeadlineRangeError,
    ProcessNotFoundError,
)
from app.shared.service_helpers import assert_author_or_admin, get_or_raise
from app.shared.uow import unit_of_work

logger = logging.getLogger(__name__)

EXPIRED_DAYS_BEFORE = -1

_DEFAULT_ALERT_INTERVALS = [30, 15, 7, 3, 2, 1]


class DeadlineService:
    def __init__(
        self,
        repository: DeadlineRepository,
        holiday_repository: ForensicHolidayRepository,
        process_repository: ProcessRepository,
        alert_repository: DeadlineAlertRepository | None = None,
        notification_service: NotificationService | None = None,
        alert_intervals: list[int] | None = None,
    ) -> None:
        self.repository = repository
        self.holiday_repository = holiday_repository
        self.process_repository = process_repository
        self.alert_repository = alert_repository
        self.notification_service = notification_service
        self.alert_intervals = sorted(alert_intervals or _DEFAULT_ALERT_INTERVALS)

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
        process = get_or_raise(
            lambda: self.process_repository.get_by_id(process_id), ProcessNotFoundError
        )

        court = process.court
        comarca = payload.comarca

        due_date, _ = self.calculate_due_date(
            start_date=payload.start_date,
            business_days=payload.business_days,
            court=court,
            comarca=comarca,
        )

        with unit_of_work(self.repository.db):
            deadline = self.repository.create(
                process_id=process_id,
                start_date=payload.start_date,
                business_days=payload.business_days,
                deadline_type=payload.deadline_type,
                due_date=due_date,
                court=court,
                comarca=comarca,
                created_by=created_by_id,
            )
        return deadline

    def list_by_process(
        self, process_id: int, page: int, limit: int
    ) -> tuple[list[Deadline], int]:
        get_or_raise(
            lambda: self.process_repository.get_by_id(process_id), ProcessNotFoundError
        )
        return self.repository.list_by_process(process_id, page=page, limit=limit)

    def update(self, deadline_id: int, payload: DeadlineUpdate) -> Deadline:
        deadline = get_or_raise(
            lambda: self.repository.get_by_id(deadline_id), DeadlineNotFoundError
        )

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

        with unit_of_work(self.repository.db):
            updated = self.repository.update(
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
        return updated

    def delete(self, deadline_id: int) -> None:
        deadline = get_or_raise(
            lambda: self.repository.get_by_id(deadline_id), DeadlineNotFoundError
        )
        with unit_of_work(self.repository.db):
            self.repository.delete(deadline)

    def business_days_until(
        self,
        due_date: date,
        today: date,
        court: str | None,
        comarca: str | None,
    ) -> int:
        if due_date <= today:
            return 0

        holidays = self.holiday_repository.list_applicable_in_range(
            start=today,
            end=due_date,
            court=court,
            comarca=comarca,
        )
        holiday_map: dict[date, ForensicHoliday] = {h.date: h for h in holidays}

        count = 0
        current = today
        while current < due_date:
            current += timedelta(days=1)
            if _is_business_day(current, holiday_map):
                count += 1
        return count

    def dispatch_alerts(self, today: date) -> int:
        if self.alert_repository is None or self.notification_service is None:
            raise RuntimeError(
                "dispatch_alerts requires alert_repository and notification_service"
            )

        sent_count = 0
        for deadline in self.repository.list_all():
            if deadline.created_by is None:
                continue

            sent_days = self.alert_repository.sent_days_for(deadline.id)

            if deadline.due_date < today:
                if EXPIRED_DAYS_BEFORE not in sent_days:
                    self._send_alert(
                        deadline,
                        EventType.DEADLINE_EXPIRED,
                        EXPIRED_DAYS_BEFORE,
                        business_days_left=None,
                    )
                    sent_count += 1
                continue

            business_days_left = self.business_days_until(
                deadline.due_date, today, deadline.court, deadline.comarca
            )
            target = _smallest_interval(self.alert_intervals, business_days_left)
            if target is not None and target not in sent_days:
                self._send_alert(
                    deadline,
                    EventType.DEADLINE_APPROACHING,
                    target,
                    business_days_left=business_days_left,
                )
                sent_count += 1

        return sent_count

    def _send_alert(
        self,
        deadline: Deadline,
        event_type: EventType,
        days_before: int,
        business_days_left: int | None,
    ) -> None:
        if self.notification_service is None or self.alert_repository is None:
            raise RuntimeError(
                "_send_alert exige notification_service e alert_repository"
            )

        process = self.process_repository.get_by_id(deadline.process_id)
        process_number = (
            format_cnj(process.number) if process else str(deadline.process_id)
        )
        payload: dict = {
            "process_number": process_number,
            "deadline_type": deadline.deadline_type,
            "due_date": deadline.due_date.isoformat(),
        }
        if business_days_left is not None:
            payload["business_days_left"] = business_days_left

        self.notification_service.notify(deadline.created_by, event_type, payload)
        # Registra o disparo mesmo se o envio falhar/estiver desabilitado:
        # o alerta não é re-tentado (limitação assumida no MVP).
        with unit_of_work(self.alert_repository.db):
            self.alert_repository.create(deadline.id, days_before)
        logger.info(
            "Deadline alert dispatched deadline_id=%s event=%s days_before=%s",
            deadline.id,
            event_type.value,
            days_before,
        )

    def list_alerts(
        self, process_id: int, deadline_id: int, current_user: User
    ) -> list[DeadlineAlert]:
        if self.alert_repository is None:
            raise RuntimeError("list_alerts requires alert_repository")

        get_or_raise(
            lambda: self.process_repository.get_by_id(process_id), ProcessNotFoundError
        )

        deadline = self.repository.get_by_id(deadline_id)
        if deadline is None or deadline.process_id != process_id:
            raise DeadlineNotFoundError()

        assert_author_or_admin(current_user, deadline.created_by)

        return self.alert_repository.list_by_deadline(deadline_id)


def _smallest_interval(intervals: list[int], business_days_left: int) -> int | None:
    applicable = [i for i in intervals if business_days_left <= i]
    return min(applicable) if applicable else None


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
