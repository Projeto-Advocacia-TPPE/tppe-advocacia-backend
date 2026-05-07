import string
from datetime import datetime, timezone
from unittest.mock import MagicMock

import bcrypt
import pytest

from app.models.user import Role, User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService
from app.utils.exceptions import EmailAlreadyExistsError, UserNotFoundError


def make_user(**kwargs) -> User:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "name": "Test User",
        "email": "test@test.com",
        "hashed_password": "hashed",
        "role": Role.USER,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    user = MagicMock(spec=User)
    for key, value in defaults.items():
        setattr(user, key, value)
    return user


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    svc = UserService.__new__(UserService)
    svc.repository = repo
    return svc


class TestListUsers:
    def test_calls_repo_with_correct_params(self, service, repo):
        repo.get_all.return_value = ([], 0)

        service.list_users(role=Role.USER, is_active=True, page=2, limit=10)

        repo.get_all.assert_called_once_with(
            role=Role.USER, is_active=True, page=2, limit=10
        )

    def test_returns_user_read_list(self, service, repo):
        users = [make_user(id=1), make_user(id=2, email="other@test.com")]
        repo.get_all.return_value = (users, 2)

        result, total = service.list_users(role=None, is_active=None, page=1, limit=20)

        assert len(result) == 2
        assert total == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_returns_empty_list_when_no_users(self, service, repo):
        repo.get_all.return_value = ([], 0)

        result, total = service.list_users(role=None, is_active=None, page=1, limit=20)

        assert result == []
        assert total == 0

    def test_passes_none_filters_to_repo(self, service, repo):
        repo.get_all.return_value = ([], 0)

        service.list_users(role=None, is_active=None, page=1, limit=20)

        repo.get_all.assert_called_once_with(
            role=None, is_active=None, page=1, limit=20
        )


class TestGetUser:
    def test_returns_user_read_when_found(self, service, repo):
        repo.get_by_id.return_value = make_user(id=5, name="Alice")

        result = service.get_user(5)

        assert result.id == 5
        assert result.name == "Alice"

    def test_raises_user_not_found_when_missing(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.get_user(999)

    def test_calls_repo_with_correct_id(self, service, repo):
        repo.get_by_id.return_value = make_user(id=7)

        service.get_user(7)

        repo.get_by_id.assert_called_once_with(7)


class TestCreateUser:
    def test_raises_when_email_already_exists(self, service, repo):
        repo.email_exists.return_value = True

        with pytest.raises(EmailAlreadyExistsError):
            service.create_user(UserCreate(name="Alice", email="alice@test.com"))

    def test_does_not_call_repo_create_when_email_exists(self, service, repo):
        repo.email_exists.return_value = True

        with pytest.raises(EmailAlreadyExistsError):
            service.create_user(UserCreate(name="Alice", email="alice@test.com"))

        repo.create.assert_not_called()

    def test_stores_hashed_password_not_plain_text(self, service, repo):
        repo.email_exists.return_value = False
        repo.create.return_value = make_user()

        service.create_user(UserCreate(name="Alice", email="alice@test.com"))

        hashed = repo.create.call_args.kwargs["hashed_password"]
        assert hashed.startswith("$2b$")

    def test_password_hash_is_valid_bcrypt(self, service, repo):
        repo.email_exists.return_value = False
        repo.create.return_value = make_user()

        service.create_user(UserCreate(name="Alice", email="alice@test.com"))

        hashed = repo.create.call_args.kwargs["hashed_password"]
        # bcrypt.checkpw doesn't raise, meaning it's a valid hash format
        assert bcrypt.checkpw(b"any", hashed.encode()) is False

    def test_always_assigns_role_user(self, service, repo):
        repo.email_exists.return_value = False
        repo.create.return_value = make_user()

        service.create_user(UserCreate(name="Alice", email="alice@test.com"))

        assert repo.create.call_args.kwargs["role"] == Role.USER

    def test_passes_name_and_email_to_repo(self, service, repo):
        repo.email_exists.return_value = False
        repo.create.return_value = make_user()

        service.create_user(UserCreate(name="Bob", email="bob@test.com"))

        kwargs = repo.create.call_args.kwargs
        assert kwargs["name"] == "Bob"
        assert kwargs["email"] == "bob@test.com"

    def test_returns_user_read_on_success(self, service, repo):
        repo.email_exists.return_value = False
        repo.create.return_value = make_user(
            id=10, name="Alice", email="alice@test.com"
        )

        result = service.create_user(UserCreate(name="Alice", email="alice@test.com"))

        assert result.id == 10
        assert result.name == "Alice"
        assert result.email == "alice@test.com"


class TestUpdateUser:
    def test_raises_user_not_found_when_missing(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.update_user(999, UserUpdate(name="New Name"))

    def test_does_not_call_repo_update_when_user_missing(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.update_user(999, UserUpdate(name="New Name"))

        repo.update.assert_not_called()

    def test_raises_email_already_exists_on_duplicate_email(self, service, repo):
        repo.get_by_id.return_value = make_user(email="original@test.com")
        repo.email_exists.return_value = True

        with pytest.raises(EmailAlreadyExistsError):
            service.update_user(1, UserUpdate(email="taken@test.com"))

    def test_does_not_check_email_conflict_when_email_unchanged(self, service, repo):
        existing = make_user(email="same@test.com")
        repo.get_by_id.return_value = existing
        repo.update.return_value = existing

        service.update_user(1, UserUpdate(email="same@test.com"))

        repo.email_exists.assert_not_called()

    def test_returns_updated_user_read(self, service, repo):
        repo.get_by_id.return_value = make_user(id=1, name="Old")
        repo.update.return_value = make_user(id=1, name="New")

        result = service.update_user(1, UserUpdate(name="New"))

        assert result.name == "New"

    def test_passes_only_non_none_fields_to_repo(self, service, repo):
        existing = make_user()
        repo.get_by_id.return_value = existing
        repo.update.return_value = existing

        service.update_user(1, UserUpdate(name="Updated"))

        updates = repo.update.call_args[0][1]
        assert "name" in updates
        assert "email" not in updates
        assert "role" not in updates
        assert "is_active" not in updates

    def test_can_deactivate_user(self, service, repo):
        repo.get_by_id.return_value = make_user(is_active=True)
        repo.update.return_value = make_user(is_active=False)

        result = service.update_user(1, UserUpdate(is_active=False))

        assert result.is_active is False

    def test_can_promote_to_admin(self, service, repo):
        repo.get_by_id.return_value = make_user(role=Role.USER)
        repo.update.return_value = make_user(role=Role.ADMIN)

        result = service.update_user(1, UserUpdate(role=Role.ADMIN))

        assert result.role == Role.ADMIN

    def test_email_conflict_check_excludes_own_id(self, service, repo):
        existing = make_user(id=1, email="original@test.com")
        repo.get_by_id.return_value = existing
        repo.email_exists.return_value = False
        repo.update.return_value = existing

        service.update_user(1, UserUpdate(email="new@test.com"))

        repo.email_exists.assert_called_once_with("new@test.com", exclude_id=1)


class TestGeneratePassword:
    def test_default_length_is_12(self):
        password = UserService._generate_password()

        assert len(password) == 12

    def test_custom_length(self):
        password = UserService._generate_password(length=20)

        assert len(password) == 20

    def test_contains_only_valid_chars(self):
        valid = set(string.ascii_letters + string.digits + "!@#$%^&*")
        password = UserService._generate_password()

        assert all(c in valid for c in password)

    def test_two_calls_produce_different_passwords(self):
        p1 = UserService._generate_password()
        p2 = UserService._generate_password()

        assert p1 != p2
