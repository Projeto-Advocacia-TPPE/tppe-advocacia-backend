import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.notifications.model import NotificationPreference
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.schema import EventType
from app.modules.users.repository import UserRepository
from app.shared.types import Role


def make_user(db: Session, email: str = "u@test.com"):
    return UserRepository(db).create(
        name="U", email=email, hashed_password="h", role=Role.USER
    )


class TestGetByUser:
    def test_returns_empty_when_no_preferences(self, db: Session):
        user = make_user(db)
        repo = NotificationPreferenceRepository(db)

        assert repo.get_by_user(user.id) == []

    def test_returns_only_users_preferences(self, db: Session):
        user_a = make_user(db, email="a@test.com")
        user_b = make_user(db, email="b@test.com")
        repo = NotificationPreferenceRepository(db)
        repo.upsert_many(user_a.id, {EventType.LEAD_ASSIGNED: False})
        repo.upsert_many(user_b.id, {EventType.TASK_ASSIGNED: False})

        a_prefs = repo.get_by_user(user_a.id)

        assert len(a_prefs) == 1
        assert a_prefs[0].event_type == EventType.LEAD_ASSIGNED


class TestUpsertMany:
    def test_creates_when_not_exists(self, db: Session):
        user = make_user(db)
        repo = NotificationPreferenceRepository(db)

        result = repo.upsert_many(
            user.id,
            {EventType.LEAD_ASSIGNED: False, EventType.TASK_ASSIGNED: True},
        )

        assert len(result) == 2
        types = {p.event_type: p.enabled for p in result}
        assert types[EventType.LEAD_ASSIGNED] is False
        assert types[EventType.TASK_ASSIGNED] is True

    def test_updates_existing_value(self, db: Session):
        user = make_user(db)
        repo = NotificationPreferenceRepository(db)
        repo.upsert_many(user.id, {EventType.LEAD_ASSIGNED: True})

        repo.upsert_many(user.id, {EventType.LEAD_ASSIGNED: False})

        result = repo.get_by_user(user.id)
        assert len(result) == 1
        assert result[0].enabled is False

    def test_partial_upsert_does_not_touch_other_events(self, db: Session):
        user = make_user(db)
        repo = NotificationPreferenceRepository(db)
        repo.upsert_many(
            user.id,
            {EventType.LEAD_ASSIGNED: False, EventType.TASK_ASSIGNED: False},
        )

        repo.upsert_many(user.id, {EventType.LEAD_ASSIGNED: True})

        stored = {p.event_type: p.enabled for p in repo.get_by_user(user.id)}
        assert stored[EventType.LEAD_ASSIGNED] is True
        assert stored[EventType.TASK_ASSIGNED] is False

    def test_unique_constraint_on_user_event(self, db: Session):
        user = make_user(db)
        db.add(
            NotificationPreference(
                user_id=user.id, event_type=EventType.LEAD_ASSIGNED, enabled=True
            )
        )
        db.commit()

        db.add(
            NotificationPreference(
                user_id=user.id, event_type=EventType.LEAD_ASSIGNED, enabled=False
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
