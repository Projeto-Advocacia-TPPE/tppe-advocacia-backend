import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def _env(**overrides: str) -> dict[str, str]:
    base = {
        "APP_ENV": "development",
        "JWT_SECRET_KEY": "x" * 64,
        "RESEND_API_KEY": "re_test",
    }
    base.update(overrides)
    return base


class TestJwtSecretValidator:
    def test_accepts_weak_secret_outside_production(self, monkeypatch):
        for key, value in _env(JWT_SECRET_KEY="your-secret-key").items():
            monkeypatch.setenv(key, value)
        Settings(_env_file=None)

    def test_rejects_known_default_in_production(self, monkeypatch):
        for key, value in _env(
            APP_ENV="production", JWT_SECRET_KEY="your-secret-key"
        ).items():
            monkeypatch.setenv(key, value)
        with pytest.raises(ValidationError) as exc:
            Settings(_env_file=None)
        assert "JWT_SECRET_KEY" in str(exc.value)

    def test_rejects_short_secret_in_production(self, monkeypatch):
        for key, value in _env(APP_ENV="production", JWT_SECRET_KEY="x" * 16).items():
            monkeypatch.setenv(key, value)
        with pytest.raises(ValidationError) as exc:
            Settings(_env_file=None)
        assert "JWT_SECRET_KEY" in str(exc.value)

    def test_accepts_strong_secret_in_production(self, monkeypatch):
        for key, value in _env(APP_ENV="production", JWT_SECRET_KEY="x" * 32).items():
            monkeypatch.setenv(key, value)
        Settings(_env_file=None)
