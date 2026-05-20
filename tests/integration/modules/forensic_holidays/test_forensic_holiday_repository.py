from datetime import date

from sqlalchemy.orm import Session

from app.modules.forensic_holidays.model import HolidayScope
from app.modules.forensic_holidays.repository import ForensicHolidayRepository


def _seed(repo: ForensicHolidayRepository) -> dict[str, int]:
    ids: dict[str, int] = {}
    ids["nat_2026"] = repo.create(
        date(2026, 5, 1), "Dia do Trabalho", HolidayScope.NATIONAL, None, None
    ).id
    ids["nat_2027"] = repo.create(
        date(2027, 1, 1), "Confraternização", HolidayScope.NATIONAL, None, None
    ).id
    ids["tjdft_2026"] = repo.create(
        date(2026, 4, 23), "Aniv Brasília", HolidayScope.COURT, "TJDFT", None
    ).id
    ids["tjsp_2026"] = repo.create(
        date(2026, 1, 25), "Aniv SP", HolidayScope.COURT, "TJSP", None
    ).id
    ids["comarca_bsb"] = repo.create(
        date(2026, 6, 10), "Festa Brasília", HolidayScope.COMARCA, None, "Brasília"
    ).id
    return ids


class TestCreate:
    def test_persists_holiday(self, db: Session):
        repo = ForensicHolidayRepository(db)
        h = repo.create(
            date(2026, 5, 1), "Dia do Trabalho", HolidayScope.NATIONAL, None, None
        )
        assert h.id is not None
        assert h.scope == HolidayScope.NATIONAL


class TestGetByNaturalKey:
    def test_distinguishes_court_from_national_same_date(self, db: Session):
        repo = ForensicHolidayRepository(db)
        repo.create(date(2026, 5, 1), "Nacional", HolidayScope.NATIONAL, None, None)
        repo.create(date(2026, 5, 1), "Court", HolidayScope.COURT, "TJDFT", None)

        nat = repo.get_by_natural_key(
            date(2026, 5, 1), HolidayScope.NATIONAL, None, None
        )
        court = repo.get_by_natural_key(
            date(2026, 5, 1), HolidayScope.COURT, "TJDFT", None
        )

        assert nat is not None and nat.description == "Nacional"
        assert court is not None and court.description == "Court"
        assert nat.id != court.id

    def test_returns_none_when_missing(self, db: Session):
        repo = ForensicHolidayRepository(db)
        assert (
            repo.get_by_natural_key(date(2026, 5, 1), HolidayScope.NATIONAL, None, None)
            is None
        )


class TestList:
    def test_no_filters_returns_all(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        items, total = repo.list(year=None, court=None, comarca=None)
        assert total == 5

    def test_year_filter(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        items, total = repo.list(year=2026, court=None, comarca=None)
        assert total == 4
        assert all(h.date.year == 2026 for h in items)

    def test_court_filter_includes_national_and_matching_court_only(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        items, total = repo.list(year=None, court="TJDFT", comarca=None)
        # NATIONAL (2) + COURT TJDFT (1) — not TJSP, not COMARCA
        assert total == 3
        scopes_courts = {(h.scope, h.court) for h in items}
        assert (HolidayScope.NATIONAL, None) in scopes_courts
        assert (HolidayScope.COURT, "TJDFT") in scopes_courts
        assert all(h.court != "TJSP" for h in items)

    def test_comarca_filter(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        items, total = repo.list(year=None, court=None, comarca="Brasília")
        # NATIONAL (2) + COMARCA Brasília (1)
        assert total == 3

    def test_combined_year_and_court(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        items, total = repo.list(year=2026, court="TJDFT", comarca=None)
        # 2026 NATIONAL (1) + 2026 TJDFT (1)
        assert total == 2

    def test_pagination(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        page1, total = repo.list(year=None, court=None, comarca=None, page=1, limit=2)
        page2, _ = repo.list(year=None, court=None, comarca=None, page=2, limit=2)
        assert total == 5
        assert len(page1) == 2
        assert len(page2) == 2
        assert {h.id for h in page1}.isdisjoint({h.id for h in page2})


class TestListApplicableInRange:
    def test_national_always_included(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        out = repo.list_applicable_in_range(
            date(2026, 1, 1), date(2026, 12, 31), court=None, comarca=None
        )
        # only NATIONAL 2026
        assert len(out) == 1
        assert out[0].scope == HolidayScope.NATIONAL

    def test_court_filter_excludes_other_courts(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        out = repo.list_applicable_in_range(
            date(2026, 1, 1), date(2026, 12, 31), court="TJDFT", comarca=None
        )
        dates = {h.date for h in out}
        assert date(2026, 5, 1) in dates  # NATIONAL
        assert date(2026, 4, 23) in dates  # TJDFT
        assert date(2026, 1, 25) not in dates  # TJSP excluded
        assert date(2026, 6, 10) not in dates  # COMARCA excluded (no comarca filter)

    def test_court_and_comarca_filter_union(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        out = repo.list_applicable_in_range(
            date(2026, 1, 1),
            date(2026, 12, 31),
            court="TJDFT",
            comarca="Brasília",
        )
        dates = {h.date for h in out}
        assert dates == {date(2026, 5, 1), date(2026, 4, 23), date(2026, 6, 10)}

    def test_range_excludes_out_of_range(self, db: Session):
        repo = ForensicHolidayRepository(db)
        _seed(repo)
        out = repo.list_applicable_in_range(
            date(2026, 1, 1), date(2026, 12, 31), court=None, comarca=None
        )
        assert all(date(2026, 1, 1) <= h.date <= date(2026, 12, 31) for h in out)


class TestUpdate:
    def test_updates_description(self, db: Session):
        repo = ForensicHolidayRepository(db)
        h = repo.create(date(2026, 5, 1), "Old", HolidayScope.NATIONAL, None, None)
        updated = repo.update(
            h,
            date_=None,
            description="New",
            scope=None,
            court=None,
            comarca=None,
            clear_court=False,
            clear_comarca=False,
        )
        assert updated.description == "New"

    def test_clears_court(self, db: Session):
        repo = ForensicHolidayRepository(db)
        h = repo.create(date(2026, 4, 23), "x", HolidayScope.COURT, "TJDFT", None)
        updated = repo.update(
            h,
            date_=None,
            description=None,
            scope=HolidayScope.NATIONAL,
            court=None,
            comarca=None,
            clear_court=True,
            clear_comarca=False,
        )
        assert updated.court is None
        assert updated.scope == HolidayScope.NATIONAL


class TestDelete:
    def test_removes_holiday(self, db: Session):
        repo = ForensicHolidayRepository(db)
        h = repo.create(date(2026, 5, 1), "x", HolidayScope.NATIONAL, None, None)
        hid = h.id
        repo.delete(h)
        assert repo.get_by_id(hid) is None
