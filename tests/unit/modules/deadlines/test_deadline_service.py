from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.modules.deadlines.schema import DeadlineCreate, DeadlineUpdate, SkipReason
from app.modules.deadlines.service import DeadlineService
from app.shared.exceptions import (
    DeadlineNotFoundError,
    InvalidDeadlineRangeError,
    ProcessNotFoundError,
)


def make_holiday(d: date, description: str) -> SimpleNamespace:
    return SimpleNamespace(date=d, description=description)


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def holidays():
    return MagicMock()


@pytest.fixture
def processes():
    return MagicMock()


@pytest.fixture
def service(repo, holidays, processes):
    return DeadlineService(
        repository=repo,
        holiday_repository=holidays,
        process_repository=processes,
        alert_repository=MagicMock(),
        notification_service=MagicMock(),
    )


class TestCalculateDueDate:
    def test_counts_business_days_no_holidays(self, service, holidays):
        holidays.list_applicable_in_range.return_value = []
        due, skipped = service.calculate_due_date(date(2026, 5, 11), 5, None, None)
        assert due == date(2026, 5, 18)  # Mon→Mon (5 business days)
        assert {s.date for s in skipped} == {date(2026, 5, 16), date(2026, 5, 17)}
        assert all(s.reason == SkipReason.WEEKEND for s in skipped)

    def test_skips_weekend_in_middle(self, service, holidays):
        holidays.list_applicable_in_range.return_value = []
        due, skipped = service.calculate_due_date(date(2026, 5, 13), 3, None, None)
        # Wed 13 -> Thu14, Fri15, skip Sat/Sun, Mon18
        assert due == date(2026, 5, 18)
        assert len(skipped) == 2
        assert all(s.reason == SkipReason.WEEKEND for s in skipped)

    def test_start_date_on_weekend_advances_to_monday(self, service, holidays):
        holidays.list_applicable_in_range.return_value = []
        due, skipped = service.calculate_due_date(date(2026, 5, 16), 1, None, None)
        # Sat16 → advances to Mon18, count 1 → Tue19
        assert due == date(2026, 5, 19)
        assert any(s.date == date(2026, 5, 16) for s in skipped)
        assert any(s.date == date(2026, 5, 17) for s in skipped)

    def test_skips_holiday_returned_by_repo(self, service, holidays):
        holidays.list_applicable_in_range.return_value = [
            make_holiday(date(2026, 5, 1), "Dia do Trabalho"),
        ]
        # Wed Apr29 → Thu30=1, Fri1(holiday)/Sat/Sun skip→Mon4=2, Tue5=3
        due, skipped = service.calculate_due_date(date(2026, 4, 29), 3, None, None)
        assert due == date(2026, 5, 5)
        holiday_skips = [s for s in skipped if s.reason == SkipReason.HOLIDAY]
        assert len(holiday_skips) == 1
        assert holiday_skips[0].description == "Dia do Trabalho"

    def test_passes_court_and_comarca_to_repo(self, service, holidays):
        holidays.list_applicable_in_range.return_value = []
        service.calculate_due_date(date(2026, 5, 11), 5, "TJDFT", "Brasília")
        kwargs = holidays.list_applicable_in_range.call_args.kwargs
        assert kwargs["court"] == "TJDFT"
        assert kwargs["comarca"] == "Brasília"

    def test_crosses_year(self, service, holidays):
        holidays.list_applicable_in_range.return_value = [
            make_holiday(date(2026, 12, 25), "Natal"),
            make_holiday(date(2027, 1, 1), "Confraternização"),
        ]
        # Mon Dec21, count 8: 22,23,24, skip25, 28,29,30,31, skipJan1, Jan4
        due, _ = service.calculate_due_date(date(2026, 12, 21), 8, None, None)
        assert due == date(2027, 1, 4)

    def test_business_days_zero_raises(self, service):
        with pytest.raises(InvalidDeadlineRangeError):
            service.calculate_due_date(date(2026, 5, 11), 0, None, None)

    def test_business_days_negative_raises(self, service):
        with pytest.raises(InvalidDeadlineRangeError):
            service.calculate_due_date(date(2026, 5, 11), -3, None, None)


class TestCreateForProcess:
    def test_raises_when_process_missing(self, service, processes):
        processes.get_by_id.return_value = None
        with pytest.raises(ProcessNotFoundError):
            service.create_for_process(
                99,
                DeadlineCreate(
                    start_date=date(2026, 5, 11),
                    business_days=5,
                    deadline_type="Contestação",
                ),
                created_by_id=10,
            )

    def test_snapshots_court_from_process_and_comarca_from_payload(
        self, service, processes, holidays, repo
    ):
        processes.get_by_id.return_value = SimpleNamespace(id=1, court="TJDFT")
        holidays.list_applicable_in_range.return_value = []
        repo.create.return_value = MagicMock()

        service.create_for_process(
            1,
            DeadlineCreate(
                start_date=date(2026, 5, 11),
                business_days=5,
                deadline_type="Contestação",
                comarca="Brasília",
            ),
            created_by_id=10,
        )

        kwargs = repo.create.call_args.kwargs
        assert kwargs["process_id"] == 1
        assert kwargs["court"] == "TJDFT"
        assert kwargs["comarca"] == "Brasília"
        assert kwargs["due_date"] == date(2026, 5, 18)
        assert kwargs["created_by"] == 10
        assert kwargs["deadline_type"] == "Contestação"


class TestListByProcess:
    def test_raises_when_process_missing(self, service, processes):
        processes.get_by_id.return_value = None
        with pytest.raises(ProcessNotFoundError):
            service.list_by_process(99, page=1, limit=20)

    def test_delegates_to_repository(self, service, processes, repo):
        processes.get_by_id.return_value = SimpleNamespace(id=1)
        repo.list_by_process.return_value = ([], 0)
        service.list_by_process(1, page=2, limit=10)
        repo.list_by_process.assert_called_once_with(1, page=2, limit=10)


class TestUpdate:
    def test_raises_when_deadline_missing(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(DeadlineNotFoundError):
            service.update(99, DeadlineUpdate(deadline_type="x"))

    def test_no_recalc_when_only_deadline_type_changes(self, service, repo, holidays):
        repo.get_by_id.return_value = SimpleNamespace(
            id=1,
            start_date=date(2026, 5, 11),
            business_days=5,
            court="TJDFT",
            comarca=None,
        )
        repo.update.return_value = MagicMock()

        service.update(1, DeadlineUpdate(deadline_type="Recurso"))

        holidays.list_applicable_in_range.assert_not_called()
        assert repo.update.call_args.kwargs["due_date"] is None

    def test_recalc_when_business_days_changes(self, service, repo, holidays):
        repo.get_by_id.return_value = SimpleNamespace(
            id=1,
            start_date=date(2026, 5, 11),
            business_days=5,
            court="TJDFT",
            comarca=None,
        )
        holidays.list_applicable_in_range.return_value = []
        repo.update.return_value = MagicMock()

        service.update(1, DeadlineUpdate(business_days=10))

        # Mon May 11 + 10 business days = Mon May 25
        assert repo.update.call_args.kwargs["due_date"] == date(2026, 5, 25)

    def test_recalc_uses_snapshot_court(self, service, repo, holidays):
        repo.get_by_id.return_value = SimpleNamespace(
            id=1,
            start_date=date(2026, 5, 11),
            business_days=5,
            court="TJDFT",
            comarca=None,
        )
        holidays.list_applicable_in_range.return_value = []
        repo.update.return_value = MagicMock()

        service.update(1, DeadlineUpdate(start_date=date(2026, 5, 12)))

        assert holidays.list_applicable_in_range.call_args.kwargs["court"] == "TJDFT"


class TestDelete:
    def test_raises_when_missing(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(DeadlineNotFoundError):
            service.delete(99)

    def test_delegates_to_repository(self, service, repo):
        deadline = SimpleNamespace(id=1)
        repo.get_by_id.return_value = deadline
        service.delete(1)
        repo.delete.assert_called_once_with(deadline)
