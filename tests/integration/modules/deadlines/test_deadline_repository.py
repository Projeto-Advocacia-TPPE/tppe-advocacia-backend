from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.modules.deadlines.repository import DeadlineRepository
from app.modules.processes.model import Process
from app.modules.processes.repository import ProcessRepository


@pytest.fixture
def process_fixture(db: Session) -> Process:
    return ProcessRepository(db).create(
        number="99999999999999999991",
        court="TJDFT",
        action_type="Ação Cível",
    )


class TestCreate:
    def test_persists_deadline(self, db: Session, process_fixture: Process):
        repo = DeadlineRepository(db)
        d = repo.create(
            process_id=process_fixture.id,
            start_date=date(2026, 5, 11),
            business_days=5,
            deadline_type="Contestação",
            due_date=date(2026, 5, 18),
            court="TJDFT",
            comarca=None,
            created_by=None,
        )
        assert d.id is not None
        assert d.due_date == date(2026, 5, 18)
        assert d.court == "TJDFT"


class TestGetById:
    def test_returns_when_exists(self, db: Session, process_fixture: Process):
        repo = DeadlineRepository(db)
        created = repo.create(
            process_id=process_fixture.id,
            start_date=date(2026, 5, 11),
            business_days=5,
            deadline_type="x",
            due_date=date(2026, 5, 18),
            court="TJDFT",
            comarca=None,
            created_by=None,
        )
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_missing(self, db: Session):
        repo = DeadlineRepository(db)
        assert repo.get_by_id(9999) is None


class TestListByProcess:
    def test_orders_by_due_date_asc(self, db: Session, process_fixture: Process):
        repo = DeadlineRepository(db)
        later = repo.create(
            process_id=process_fixture.id,
            start_date=date(2026, 5, 11),
            business_days=10,
            deadline_type="b",
            due_date=date(2026, 5, 25),
            court="TJDFT",
            comarca=None,
            created_by=None,
        )
        earlier = repo.create(
            process_id=process_fixture.id,
            start_date=date(2026, 5, 11),
            business_days=5,
            deadline_type="a",
            due_date=date(2026, 5, 18),
            court="TJDFT",
            comarca=None,
            created_by=None,
        )

        items, total = repo.list_by_process(process_fixture.id)
        assert total == 2
        assert items[0].id == earlier.id
        assert items[1].id == later.id

    def test_scoped_to_process(self, db: Session, process_fixture: Process):
        other = ProcessRepository(db).create(
            number="99999999999999999992", court="TJSP", action_type="x"
        )
        repo = DeadlineRepository(db)
        repo.create(
            process_id=process_fixture.id,
            start_date=date(2026, 5, 11),
            business_days=5,
            deadline_type="mine",
            due_date=date(2026, 5, 18),
            court="TJDFT",
            comarca=None,
            created_by=None,
        )
        repo.create(
            process_id=other.id,
            start_date=date(2026, 5, 11),
            business_days=5,
            deadline_type="other",
            due_date=date(2026, 5, 18),
            court="TJSP",
            comarca=None,
            created_by=None,
        )

        items, total = repo.list_by_process(process_fixture.id)
        assert total == 1
        assert items[0].deadline_type == "mine"

    def test_pagination(self, db: Session, process_fixture: Process):
        repo = DeadlineRepository(db)
        for i in range(5):
            repo.create(
                process_id=process_fixture.id,
                start_date=date(2026, 5, 11),
                business_days=i + 1,
                deadline_type=f"d{i}",
                due_date=date(2026, 5, 12 + i),
                court="TJDFT",
                comarca=None,
                created_by=None,
            )

        page1, total = repo.list_by_process(process_fixture.id, page=1, limit=2)
        page2, _ = repo.list_by_process(process_fixture.id, page=2, limit=2)
        assert total == 5
        assert len(page1) == 2
        assert len(page2) == 2
        assert {d.id for d in page1}.isdisjoint({d.id for d in page2})


class TestUpdate:
    def test_recalc_fields(self, db: Session, process_fixture: Process):
        repo = DeadlineRepository(db)
        d = repo.create(
            process_id=process_fixture.id,
            start_date=date(2026, 5, 11),
            business_days=5,
            deadline_type="x",
            due_date=date(2026, 5, 18),
            court="TJDFT",
            comarca=None,
            created_by=None,
        )
        updated = repo.update(
            d,
            start_date=date(2026, 5, 12),
            business_days=10,
            deadline_type=None,
            comarca="Brasília",
            due_date=date(2026, 5, 26),
            clear_comarca=False,
        )
        assert updated.start_date == date(2026, 5, 12)
        assert updated.business_days == 10
        assert updated.due_date == date(2026, 5, 26)
        assert updated.comarca == "Brasília"

    def test_clears_comarca(self, db: Session, process_fixture: Process):
        repo = DeadlineRepository(db)
        d = repo.create(
            process_id=process_fixture.id,
            start_date=date(2026, 5, 11),
            business_days=5,
            deadline_type="x",
            due_date=date(2026, 5, 18),
            court="TJDFT",
            comarca="Brasília",
            created_by=None,
        )
        updated = repo.update(
            d,
            start_date=None,
            business_days=None,
            deadline_type=None,
            comarca=None,
            due_date=None,
            clear_comarca=True,
        )
        assert updated.comarca is None


class TestDelete:
    def test_removes_deadline(self, db: Session, process_fixture: Process):
        repo = DeadlineRepository(db)
        d = repo.create(
            process_id=process_fixture.id,
            start_date=date(2026, 5, 11),
            business_days=5,
            deadline_type="x",
            due_date=date(2026, 5, 18),
            court="TJDFT",
            comarca=None,
            created_by=None,
        )
        did = d.id
        repo.delete(d)
        assert repo.get_by_id(did) is None
