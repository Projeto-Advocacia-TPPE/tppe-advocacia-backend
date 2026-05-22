from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.modules.appointments.model import AppointmentType
from app.modules.appointments.repository import AppointmentRepository
from app.modules.users.repository import UserRepository
from app.shared.types import Role


@pytest.fixture
def user_id(db: Session) -> int:
    user = UserRepository(db).create(
        name="Owner",
        email="owner@test.com",
        hashed_password="x",
        role=Role.USER,
    )
    return user.id


@pytest.fixture
def other_user_id(db: Session) -> int:
    user = UserRepository(db).create(
        name="Other",
        email="other@test.com",
        hashed_password="x",
        role=Role.USER,
    )
    return user.id


def create_appointment(repo: AppointmentRepository, created_by: int, **overrides):
    data = {
        "title": "Compromisso",
        "type": AppointmentType.REUNIAO,
        "starts_at": datetime(2026, 12, 1, 14, 0, tzinfo=timezone.utc),
        "duration_minutes": 60,
        "description": None,
        "location": None,
        "client_id": None,
        "process_id": None,
        "created_by": created_by,
    }
    data.update(overrides)
    return repo.create(**data)


class TestCreateAndGet:
    def test_persists_and_loads_creator(self, db: Session, user_id: int):
        repo = AppointmentRepository(db)
        appt = create_appointment(repo, user_id, title="Audiência")
        assert appt.id is not None
        found = repo.get_by_id(appt.id)
        assert found.title == "Audiência"
        assert found.creator.id == user_id
        assert found.is_synced_to_google is False
        assert found.google_event_id is None

    def test_get_missing_returns_none(self, db: Session):
        assert AppointmentRepository(db).get_by_id(9999) is None


class TestList:
    def test_scoped_to_created_by(self, db: Session, user_id: int, other_user_id: int):
        repo = AppointmentRepository(db)
        create_appointment(repo, user_id, title="mine")
        create_appointment(repo, other_user_id, title="theirs")

        items, total = repo.list(created_by=user_id)
        assert total == 1
        assert items[0].title == "mine"

    def test_filters_by_type(self, db: Session, user_id: int):
        repo = AppointmentRepository(db)
        create_appointment(repo, user_id, type=AppointmentType.AUDIENCIA)
        create_appointment(repo, user_id, type=AppointmentType.REUNIAO)

        items, total = repo.list(created_by=user_id, type=AppointmentType.AUDIENCIA)
        assert total == 1
        assert items[0].type == AppointmentType.AUDIENCIA

    def test_filters_by_date_range(self, db: Session, user_id: int):
        repo = AppointmentRepository(db)
        create_appointment(
            repo, user_id, starts_at=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
        )
        create_appointment(
            repo, user_id, starts_at=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        )

        items, total = repo.list(
            created_by=user_id,
            date_from=datetime(2026, 8, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )
        assert total == 1
        assert items[0].starts_at.month == 9

    def test_orders_by_starts_at_asc(self, db: Session, user_id: int):
        repo = AppointmentRepository(db)
        create_appointment(
            repo, user_id, starts_at=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        )
        create_appointment(
            repo, user_id, starts_at=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
        )
        items, _ = repo.list(created_by=user_id)
        assert items[0].starts_at.month == 6
        assert items[1].starts_at.month == 9

    def test_pagination(self, db: Session, user_id: int):
        repo = AppointmentRepository(db)
        for i in range(5):
            create_appointment(
                repo,
                user_id,
                starts_at=datetime(2026, 6, 1 + i, 9, 0, tzinfo=timezone.utc),
            )
        page1, total = repo.list(created_by=user_id, page=1, limit=2)
        page2, _ = repo.list(created_by=user_id, page=2, limit=2)
        assert total == 5
        assert len(page1) == 2
        assert {a.id for a in page1}.isdisjoint({a.id for a in page2})


class TestListUnsyncedFuture:
    def test_returns_only_future_unsynced(self, db: Session, user_id: int):
        repo = AppointmentRepository(db)
        now = datetime(2026, 11, 1, tzinfo=timezone.utc)

        future_unsynced = create_appointment(
            repo, user_id, starts_at=datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
        )
        # passado -> ignorado
        create_appointment(
            repo, user_id, starts_at=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
        )
        # futuro mas já sincronizado -> ignorado
        synced = create_appointment(
            repo, user_id, starts_at=datetime(2026, 12, 5, 9, 0, tzinfo=timezone.utc)
        )
        repo.update(synced, {"is_synced_to_google": True, "google_event_id": "evt"})

        result = repo.list_unsynced_future(user_id, now)
        assert [a.id for a in result] == [future_unsynced.id]

    def test_scoped_to_user(self, db: Session, user_id: int, other_user_id: int):
        repo = AppointmentRepository(db)
        now = datetime(2026, 11, 1, tzinfo=timezone.utc)
        mine = create_appointment(repo, user_id)
        create_appointment(repo, other_user_id)

        result = repo.list_unsynced_future(user_id, now)
        assert [a.id for a in result] == [mine.id]


class TestUpdate:
    def test_update_applies_fields(self, db: Session, user_id: int):
        repo = AppointmentRepository(db)
        appt = create_appointment(repo, user_id)
        updated = repo.update(appt, {"title": "novo título", "location": "Sala 3"})
        assert updated.title == "novo título"
        assert updated.location == "Sala 3"


class TestDelete:
    def test_delete_removes(self, db: Session, user_id: int):
        repo = AppointmentRepository(db)
        appt = create_appointment(repo, user_id)
        appt_id = appt.id
        repo.delete(appt)
        assert repo.get_by_id(appt_id) is None
