from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.modules.forensic_holidays.model import HolidayScope
from app.modules.forensic_holidays.schema import HolidayCreate, HolidayUpdate
from app.modules.forensic_holidays.service import ForensicHolidayService
from app.shared.exceptions import (
    ForensicHolidayNotFoundError,
    InvalidHolidayScopeError,
)


def make_holiday(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "date": date(2026, 5, 1),
        "description": "Dia do Trabalho",
        "scope": HolidayScope.NATIONAL,
        "court": None,
        "comarca": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    return ForensicHolidayService(repository=repo)


class TestCreate:
    def test_delegates_to_repository(self, service, repo):
        created = make_holiday()
        repo.create.return_value = created
        payload = HolidayCreate(
            date=date(2026, 5, 1),
            description="Dia do Trabalho",
            scope=HolidayScope.NATIONAL,
        )

        result = service.create(payload)

        assert result is created
        kwargs = repo.create.call_args.kwargs
        assert kwargs["scope"] == HolidayScope.NATIONAL
        assert kwargs["description"] == "Dia do Trabalho"

    def test_passes_court_for_court_scope(self, service, repo):
        repo.create.return_value = make_holiday()
        payload = HolidayCreate(
            date=date(2026, 4, 23),
            description="Aniv Brasília",
            scope=HolidayScope.COURT,
            court="TJDFT",
        )

        service.create(payload)

        assert repo.create.call_args.kwargs["court"] == "TJDFT"


class TestGet:
    def test_returns_holiday_when_exists(self, service, repo):
        holiday = make_holiday()
        repo.get_by_id.return_value = holiday
        assert service.get(1) is holiday

    def test_raises_when_missing(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(ForensicHolidayNotFoundError):
            service.get(99)


class TestList:
    def test_delegates_to_repository(self, service, repo):
        repo.list.return_value = ([], 0)
        service.list(year=2026, court="TJDFT", comarca=None, page=2, limit=50)
        repo.list.assert_called_once_with(2026, "TJDFT", None, page=2, limit=50)


class TestUpdate:
    def test_raises_when_missing(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(ForensicHolidayNotFoundError):
            service.update(99, HolidayUpdate(description="x"))

    def test_updates_description(self, service, repo):
        repo.get_by_id.return_value = make_holiday()
        repo.update.return_value = make_holiday(description="New")

        service.update(1, HolidayUpdate(description="New"))

        assert repo.update.call_args.kwargs["description"] == "New"

    def test_rejects_scope_change_to_court_without_court(self, service, repo):
        repo.get_by_id.return_value = make_holiday(scope=HolidayScope.NATIONAL)
        with pytest.raises(InvalidHolidayScopeError):
            service.update(1, HolidayUpdate(scope=HolidayScope.COURT))

    def test_rejects_national_scope_with_existing_court(self, service, repo):
        # holiday already has court; changing scope to NATIONAL without clearing court
        repo.get_by_id.return_value = make_holiday(
            scope=HolidayScope.COURT, court="TJDFT"
        )
        with pytest.raises(InvalidHolidayScopeError):
            service.update(1, HolidayUpdate(scope=HolidayScope.NATIONAL))

    def test_allows_scope_change_to_national_when_clearing_court(self, service, repo):
        repo.get_by_id.return_value = make_holiday(
            scope=HolidayScope.COURT, court="TJDFT"
        )
        repo.update.return_value = make_holiday(scope=HolidayScope.NATIONAL)

        service.update(1, HolidayUpdate(scope=HolidayScope.NATIONAL, court=None))

        assert repo.update.call_args.kwargs["clear_court"] is True


class TestDelete:
    def test_raises_when_missing(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(ForensicHolidayNotFoundError):
            service.delete(99)

    def test_delegates_to_repository(self, service, repo):
        holiday = make_holiday()
        repo.get_by_id.return_value = holiday
        service.delete(1)
        repo.delete.assert_called_once_with(holiday)
