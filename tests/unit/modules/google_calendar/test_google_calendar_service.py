from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet

from app.modules.google_calendar.crypto import TokenCipher
from app.modules.google_calendar.fake_service import FakeGoogleCalendarClient
from app.modules.google_calendar.service import (
    SYNC_CREATE,
    SYNC_DELETE,
    SYNC_UPDATE,
    GoogleCalendarService,
    GoogleOAuthError,
)
from app.shared.exceptions import GoogleNotConfiguredError

SECRET = "unit-test-state-secret"
REFRESH_TOKEN = "1//0-refresh-token"


def make_appointment(**overrides) -> SimpleNamespace:
    data = {
        "id": 1,
        "created_by": 7,
        "title": "Reunião",
        "description": "pauta",
        "location": "Sala 1",
        "starts_at": datetime(2026, 12, 1, 14, 0, tzinfo=timezone.utc),
        "duration_minutes": 60,
        "google_event_id": None,
        "is_synced_to_google": False,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.fixture
def cipher() -> TokenCipher:
    return TokenCipher(Fernet.generate_key().decode())


@pytest.fixture
def client() -> FakeGoogleCalendarClient:
    return FakeGoogleCalendarClient()


@pytest.fixture
def repo():
    return MagicMock()


def make_service(repo, client, cipher, oauth=None) -> GoogleCalendarService:
    return GoogleCalendarService(repo, client, oauth, cipher, SECRET)


def connected_credential(cipher: TokenCipher) -> SimpleNamespace:
    return SimpleNamespace(
        encrypted_refresh_token=cipher.encrypt(REFRESH_TOKEN),
        scope="calendar.events",
        connected_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )


class TestSyncAppointment:
    def test_create_pushes_event_and_returns_id(self, repo, client, cipher):
        repo.get_by_user.return_value = connected_credential(cipher)
        service = make_service(repo, client, cipher)

        event_id = service.sync_appointment(make_appointment(), SYNC_CREATE)

        assert event_id == "fake-event-1"
        assert event_id in client.events

    def test_skips_when_user_not_connected(self, repo, client, cipher):
        repo.get_by_user.return_value = None
        service = make_service(repo, client, cipher)

        assert service.sync_appointment(make_appointment(), SYNC_CREATE) is None
        assert client.events == {}

    def test_skips_when_not_configured(self, repo, client):
        service = make_service(repo, client, cipher=None)
        assert service.sync_appointment(make_appointment(), SYNC_CREATE) is None

    def test_failure_is_swallowed(self, repo, client, cipher):
        repo.get_by_user.return_value = connected_credential(cipher)
        client.fail = True
        service = make_service(repo, client, cipher)

        assert service.sync_appointment(make_appointment(), SYNC_CREATE) is None

    def test_update_existing_event_keeps_id(self, repo, client, cipher):
        repo.get_by_user.return_value = connected_credential(cipher)
        service = make_service(repo, client, cipher)
        appointment = make_appointment(google_event_id="evt-existing")

        result = service.sync_appointment(appointment, SYNC_UPDATE)

        assert result == "evt-existing"
        assert client.events["evt-existing"]["summary"] == "Reunião"

    def test_update_unsynced_appointment_creates_event(self, repo, client, cipher):
        repo.get_by_user.return_value = connected_credential(cipher)
        service = make_service(repo, client, cipher)

        result = service.sync_appointment(make_appointment(), SYNC_UPDATE)

        assert result == "fake-event-1"

    def test_delete_removes_event(self, repo, client, cipher):
        repo.get_by_user.return_value = connected_credential(cipher)
        client.events["evt-1"] = {"summary": "x"}
        service = make_service(repo, client, cipher)

        result = service.sync_appointment(
            make_appointment(google_event_id="evt-1"), SYNC_DELETE
        )

        assert result is None
        assert "evt-1" not in client.events


class TestStatus:
    def test_reports_connected(self, repo, client, cipher):
        repo.get_by_user.return_value = connected_credential(cipher)
        status = make_service(repo, client, cipher).get_status(7)
        assert status.connected is True
        assert status.scope == "calendar.events"

    def test_reports_disconnected(self, repo, client, cipher):
        repo.get_by_user.return_value = None
        status = make_service(repo, client, cipher).get_status(7)
        assert status.connected is False
        assert status.connected_at is None

    def test_disconnect_delegates_to_repo(self, repo, client, cipher):
        make_service(repo, client, cipher).disconnect(7)
        repo.delete_by_user.assert_called_once_with(7)


class TestAuthUrl:
    def test_raises_when_not_configured(self, repo, client, cipher):
        service = make_service(repo, client, cipher, oauth=None)
        with pytest.raises(GoogleNotConfiguredError):
            service.build_auth_url(7)

    def test_builds_url_with_signed_state(self, repo, client, cipher):
        oauth = MagicMock()
        oauth.build_auth_url.return_value = "https://accounts.google.com/o/oauth2/auth"
        service = make_service(repo, client, cipher, oauth=oauth)

        url = service.build_auth_url(7)

        assert url == "https://accounts.google.com/o/oauth2/auth"
        state = oauth.build_auth_url.call_args.args[0]
        assert service._decode_state(state) == 7


class TestCallback:
    def test_stores_encrypted_token(self, repo, client, cipher):
        oauth = MagicMock()
        oauth.exchange_code.return_value = (REFRESH_TOKEN, "calendar.events")
        service = make_service(repo, client, cipher, oauth=oauth)
        state = service._encode_state(7)

        user_id = service.handle_callback("auth-code", state)

        assert user_id == 7
        kwargs = repo.upsert.call_args.kwargs
        assert kwargs["user_id"] == 7
        assert cipher.decrypt(kwargs["encrypted_refresh_token"]) == REFRESH_TOKEN

    def test_rejects_invalid_state(self, repo, client, cipher):
        oauth = MagicMock()
        service = make_service(repo, client, cipher, oauth=oauth)
        with pytest.raises(GoogleOAuthError):
            service.handle_callback("auth-code", "tampered-state")

    def test_rejects_when_no_refresh_token(self, repo, client, cipher):
        oauth = MagicMock()
        oauth.exchange_code.return_value = (None, "calendar.events")
        service = make_service(repo, client, cipher, oauth=oauth)
        state = service._encode_state(7)
        with pytest.raises(GoogleOAuthError):
            service.handle_callback("auth-code", state)


class TestState:
    def test_encode_decode_roundtrip(self, repo, client, cipher):
        service = make_service(repo, client, cipher)
        assert service._decode_state(service._encode_state(42)) == 42

    def test_decode_rejects_garbage(self, repo, client, cipher):
        service = make_service(repo, client, cipher)
        with pytest.raises(GoogleOAuthError):
            service._decode_state("not-a-jwt")
