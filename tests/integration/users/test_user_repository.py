from sqlalchemy.orm import Session

from app.modules.users.model import Role
from app.modules.users.repository import UserRepository


def make_user(
    repo: UserRepository, *, name="Test", email="test@test.com", role=Role.USER
):
    return repo.create(
        name=name,
        email=email,
        hashed_password="hashed",
        role=role,
    )


class TestCreate:
    def test_creates_user_with_correct_fields(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo, name="Alice", email="alice@test.com", role=Role.ADMIN)

        assert user.id is not None
        assert user.name == "Alice"
        assert user.email == "alice@test.com"
        assert user.role == Role.ADMIN
        assert user.is_active is True

    def test_default_role_is_user(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo, role=Role.USER)

        assert user.role == Role.USER


class TestGetById:
    def test_returns_user_when_exists(self, db: Session):
        repo = UserRepository(db)
        created = make_user(repo)

        found = repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_not_exists(self, db: Session):
        repo = UserRepository(db)

        assert repo.get_by_id(999) is None


class TestGetByEmail:
    def test_returns_user_when_email_matches(self, db: Session):
        repo = UserRepository(db)
        make_user(repo, email="find@test.com")

        found = repo.get_by_email("find@test.com")

        assert found is not None
        assert found.email == "find@test.com"

    def test_returns_none_when_email_not_found(self, db: Session):
        repo = UserRepository(db)

        assert repo.get_by_email("ghost@test.com") is None


class TestEmailExists:
    def test_returns_true_when_email_taken(self, db: Session):
        repo = UserRepository(db)
        make_user(repo, email="taken@test.com")

        assert repo.email_exists("taken@test.com") is True

    def test_returns_false_when_email_free(self, db: Session):
        repo = UserRepository(db)

        assert repo.email_exists("free@test.com") is False

    def test_excludes_own_id(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo, email="own@test.com")

        assert repo.email_exists("own@test.com", exclude_id=user.id) is False

    def test_detects_conflict_with_other_user(self, db: Session):
        repo = UserRepository(db)
        make_user(repo, email="conflict@test.com")
        other = make_user(repo, email="other@test.com")

        assert repo.email_exists("conflict@test.com", exclude_id=other.id) is True


class TestGetAll:
    def test_returns_all_users(self, db: Session):
        repo = UserRepository(db)
        make_user(repo, email="a@test.com")
        make_user(repo, email="b@test.com")

        users, total = repo.get_all()

        assert total == 2
        assert len(users) == 2

    def test_filters_by_role(self, db: Session):
        repo = UserRepository(db)
        make_user(repo, email="admin@test.com", role=Role.ADMIN)
        make_user(repo, email="user@test.com", role=Role.USER)

        users, total = repo.get_all(role=Role.ADMIN)

        assert total == 1
        assert users[0].role == Role.ADMIN

    def test_filters_by_is_active(self, db: Session):
        repo = UserRepository(db)
        active = make_user(repo, email="active@test.com")
        inactive = make_user(repo, email="inactive@test.com")
        repo.update(inactive, {"is_active": False})

        users, total = repo.get_all(is_active=True)

        assert total == 1
        assert users[0].id == active.id

    def test_pagination_respects_limit(self, db: Session):
        repo = UserRepository(db)
        for i in range(5):
            make_user(repo, email=f"u{i}@test.com")

        users, total = repo.get_all(page=1, limit=2)

        assert total == 5
        assert len(users) == 2

    def test_pagination_second_page(self, db: Session):
        repo = UserRepository(db)
        for i in range(5):
            make_user(repo, email=f"u{i}@test.com")

        users_p1, _ = repo.get_all(page=1, limit=3)
        users_p2, _ = repo.get_all(page=2, limit=3)

        ids_p1 = {u.id for u in users_p1}
        ids_p2 = {u.id for u in users_p2}
        assert ids_p1.isdisjoint(ids_p2)

    def test_returns_empty_when_no_users(self, db: Session):
        repo = UserRepository(db)

        users, total = repo.get_all()

        assert total == 0
        assert users == []


class TestGetByResetTokenHash:
    def test_returns_user_when_hash_matches(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo, email="reset@test.com")
        repo.update(user, {"reset_token_hash": "abc123hash"})

        found = repo.get_by_reset_token_hash("abc123hash")

        assert found is not None
        assert found.id == user.id

    def test_returns_none_when_hash_not_found(self, db: Session):
        repo = UserRepository(db)

        assert repo.get_by_reset_token_hash("nonexistent") is None

    def test_returns_none_after_token_is_cleared(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo, email="cleared@test.com")
        repo.update(user, {"reset_token_hash": "willbecleared"})
        repo.update(user, {"reset_token_hash": None})

        assert repo.get_by_reset_token_hash("willbecleared") is None


class TestUpdate:
    def test_updates_name(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo, name="Before")

        updated = repo.update(user, {"name": "After"})

        assert updated.name == "After"

    def test_updates_role(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo, role=Role.USER)

        updated = repo.update(user, {"role": Role.ADMIN})

        assert updated.role == Role.ADMIN

    def test_updates_is_active(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo)

        updated = repo.update(user, {"is_active": False})

        assert updated.is_active is False

    def test_partial_update_does_not_touch_other_fields(self, db: Session):
        repo = UserRepository(db)
        user = make_user(repo, name="Keep", email="keep@test.com")

        repo.update(user, {"name": "Changed"})

        refreshed = repo.get_by_id(user.id)
        assert refreshed.email == "keep@test.com"
