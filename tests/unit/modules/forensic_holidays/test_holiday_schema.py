from datetime import date

import pytest

from app.modules.forensic_holidays.model import HolidayScope
from app.modules.forensic_holidays.schema import HolidayCreate
from app.shared.exceptions import InvalidHolidayScopeError


class TestHolidayCreateScopeValidation:
    def test_national_with_court_rejected(self):
        with pytest.raises(InvalidHolidayScopeError):
            HolidayCreate(
                date=date(2026, 5, 1),
                description="x",
                scope=HolidayScope.NATIONAL,
                court="TJDFT",
            )

    def test_national_with_comarca_rejected(self):
        with pytest.raises(InvalidHolidayScopeError):
            HolidayCreate(
                date=date(2026, 5, 1),
                description="x",
                scope=HolidayScope.NATIONAL,
                comarca="Brasília",
            )

    def test_court_requires_court(self):
        with pytest.raises(InvalidHolidayScopeError):
            HolidayCreate(
                date=date(2026, 5, 1),
                description="x",
                scope=HolidayScope.COURT,
            )

    def test_court_with_comarca_rejected(self):
        with pytest.raises(InvalidHolidayScopeError):
            HolidayCreate(
                date=date(2026, 5, 1),
                description="x",
                scope=HolidayScope.COURT,
                court="TJDFT",
                comarca="X",
            )

    def test_comarca_requires_comarca(self):
        with pytest.raises(InvalidHolidayScopeError):
            HolidayCreate(
                date=date(2026, 5, 1),
                description="x",
                scope=HolidayScope.COMARCA,
            )

    def test_valid_national(self):
        h = HolidayCreate(
            date=date(2026, 5, 1), description="x", scope=HolidayScope.NATIONAL
        )
        assert h.scope == HolidayScope.NATIONAL

    def test_valid_court(self):
        h = HolidayCreate(
            date=date(2026, 4, 23),
            description="x",
            scope=HolidayScope.COURT,
            court="TJDFT",
        )
        assert h.court == "TJDFT"

    def test_valid_comarca(self):
        h = HolidayCreate(
            date=date(2026, 6, 10),
            description="x",
            scope=HolidayScope.COMARCA,
            comarca="Brasília",
        )
        assert h.comarca == "Brasília"
