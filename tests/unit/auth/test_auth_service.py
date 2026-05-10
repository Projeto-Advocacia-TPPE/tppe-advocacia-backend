from unittest.mock import MagicMock

import bcrypt
import jwt
import pytest

from app.modules.auth.schema import LoginRequest
from app.modules.auth.service import AuthService
from app.modules.users.model import Role, User
from app.shared.exceptions import InactiveUserError, InvalidCredentialsError


def make_user(**kwargs) -> User:
    defaults = {
        "id": 1,
        "name": "Test User",
        "email": "test@test.com",
        "hashed_password": bcrypt.hashpw(
            b"correct_password", bcrypt.gensalt()
        ).decode(),
        "role": Role.USER,
        "is_active": True,
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
    svc = AuthService.__new__(AuthService)
    svc.repository = repo
    return svc


def make_payload(password="correct_password"):
    return LoginRequest(email="test@test.com", password=password)


class TestLogin:
    def test_raises_when_user_not_found(self, service, repo):
        repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsError):
            service.login(make_payload())

    def test_does_not_leak_not_found_vs_wrong_password(self, service, repo):
        repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsError):
            service.login(make_payload("wrong"))

    def test_raises_on_wrong_password(self, service, repo):
        repo.get_by_email.return_value = make_user()

        with pytest.raises(InvalidCredentialsError):
            service.login(make_payload("wrong_password"))

    def test_does_not_raise_on_correct_password(self, service, repo):
        repo.get_by_email.return_value = make_user()

        result = service.login(make_payload("correct_password"))

        assert result.access_token is not None

    def test_raises_when_user_inactive(self, service, repo):
        repo.get_by_email.return_value = make_user(is_active=False)

        with pytest.raises(InactiveUserError):
            service.login(make_payload())

    def test_inactive_check_happens_after_password_check(self, service, repo):
        repo.get_by_email.return_value = make_user(is_active=False)

        with pytest.raises(InactiveUserError):
            service.login(make_payload("correct_password"))

    def test_returns_token_response(self, service, repo):
        repo.get_by_email.return_value = make_user()

        result = service.login(make_payload())

        assert result.token_type == "bearer"
        assert isinstance(result.access_token, str)
        assert len(result.access_token) > 0

    def test_token_contains_user_id(self, service, repo):
        from app.config.settings import get_settings

        settings = get_settings()
        repo.get_by_email.return_value = make_user(id=42)

        result = service.login(make_payload())

        payload = jwt.decode(
            result.access_token, settings.jwt_secret_key, algorithms=["HS256"]
        )
        assert payload["sub"] == "42"

    def test_token_contains_role(self, service, repo):
        from app.config.settings import get_settings

        settings = get_settings()
        repo.get_by_email.return_value = make_user(role=Role.ADMIN)

        result = service.login(make_payload())

        payload = jwt.decode(
            result.access_token, settings.jwt_secret_key, algorithms=["HS256"]
        )
        assert payload["role"] == "ADMIN"

    def test_token_contains_expiry(self, service, repo):
        from app.config.settings import get_settings

        settings = get_settings()
        repo.get_by_email.return_value = make_user()

        result = service.login(make_payload())

        payload = jwt.decode(
            result.access_token, settings.jwt_secret_key, algorithms=["HS256"]
        )
        assert "exp" in payload
