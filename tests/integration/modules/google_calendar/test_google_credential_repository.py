import pytest
from sqlalchemy.orm import Session

from app.modules.google_calendar.repository import GoogleCredentialRepository
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


class TestUpsert:
    def test_inserts_new_credential(self, db: Session, user_id: int):
        repo = GoogleCredentialRepository(db)
        credential = repo.upsert(user_id, "enc-token", "calendar.events")
        assert credential.id is not None
        assert credential.user_id == user_id
        assert credential.encrypted_refresh_token == "enc-token"
        assert credential.scope == "calendar.events"
        assert credential.connected_at is not None

    def test_updates_existing_credential_in_place(self, db: Session, user_id: int):
        repo = GoogleCredentialRepository(db)
        first = repo.upsert(user_id, "enc-token-1", "scope-1")
        second = repo.upsert(user_id, "enc-token-2", "scope-2")

        assert second.id == first.id  # mesma linha — não duplica
        assert second.encrypted_refresh_token == "enc-token-2"
        assert second.scope == "scope-2"


class TestGetByUser:
    def test_returns_credential_when_exists(self, db: Session, user_id: int):
        repo = GoogleCredentialRepository(db)
        repo.upsert(user_id, "enc-token", "scope")
        found = repo.get_by_user(user_id)
        assert found is not None
        assert found.user_id == user_id

    def test_returns_none_when_missing(self, db: Session):
        assert GoogleCredentialRepository(db).get_by_user(9999) is None


class TestDeleteByUser:
    def test_removes_and_reports_true(self, db: Session, user_id: int):
        repo = GoogleCredentialRepository(db)
        repo.upsert(user_id, "enc-token", "scope")
        assert repo.delete_by_user(user_id) is True
        assert repo.get_by_user(user_id) is None

    def test_returns_false_when_nothing_to_delete(self, db: Session):
        assert GoogleCredentialRepository(db).delete_by_user(9999) is False
