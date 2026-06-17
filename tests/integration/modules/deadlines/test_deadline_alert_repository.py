from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.deadlines.repository import (
    DeadlineAlertRepository,
    DeadlineRepository,
)
from app.modules.deadlines.service import EXPIRED_DAYS_BEFORE
from app.modules.processes.model import Process
from app.modules.processes.repository import ProcessRepository


@pytest.fixture
def deadline_id(db: Session) -> int:
    process: Process = ProcessRepository(db).create(
        number="99999999999999999991",
        court="TJDFT",
        action_type="Ação Cível",
    )
    deadline = DeadlineRepository(db).create(
        process_id=process.id,
        start_date=date(2026, 5, 11),
        business_days=5,
        deadline_type="Contestação",
        due_date=date(2026, 5, 18),
        court="TJDFT",
        comarca=None,
        created_by=None,
    )
    return deadline.id


class TestCreateAndSentDays:
    def test_persists_alert(self, db: Session, deadline_id: int):
        repo = DeadlineAlertRepository(db)
        alert = repo.create(deadline_id, 7)
        assert alert.id is not None
        assert alert.days_before == 7
        assert alert.sent_at is not None

    def test_sent_days_for_returns_set(self, db: Session, deadline_id: int):
        repo = DeadlineAlertRepository(db)
        repo.create(deadline_id, 15)
        repo.create(deadline_id, 7)
        repo.create(deadline_id, EXPIRED_DAYS_BEFORE)
        assert repo.sent_days_for(deadline_id) == {15, 7, EXPIRED_DAYS_BEFORE}

    def test_sent_days_empty_for_unknown(self, db: Session):
        assert DeadlineAlertRepository(db).sent_days_for(9999) == set()


class TestUniqueConstraint:
    def test_rejects_duplicate_deadline_days(self, db: Session, deadline_id: int):
        repo = DeadlineAlertRepository(db)
        repo.create(deadline_id, 7)
        with pytest.raises(IntegrityError):
            repo.create(deadline_id, 7)


class TestListByDeadline:
    def test_scoped_and_ordered(self, db: Session, deadline_id: int):
        repo = DeadlineAlertRepository(db)
        repo.create(deadline_id, 15)
        repo.create(deadline_id, 7)
        items = repo.list_by_deadline(deadline_id)
        assert [a.days_before for a in items] == [15, 7]
