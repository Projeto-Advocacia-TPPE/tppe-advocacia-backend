from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.modules.appointments.model import AppointmentType
from app.modules.appointments.schema import AppointmentCreate, AppointmentUpdate
from app.modules.appointments.service import AppointmentService
from app.shared.exceptions import (
    AppointmentClientNotFoundError,
    AppointmentNotFoundError,
    AppointmentProcessNotFoundError,
    ForbiddenError,
    GoogleNotConfiguredError,
    GoogleNotConnectedError,
)
from app.shared.types import Role

FUTURE = datetime.now(timezone.utc) + timedelta(days=30)


def make_user(id: int = 1, role: Role = Role.USER) -> SimpleNamespace:
    return SimpleNamespace(id=id, role=role)


def make_payload(**overrides) -> AppointmentCreate:
    data = {
        "title": "Reunião com cliente",
        "type": AppointmentType.REUNIAO,
        "starts_at": FUTURE,
        "duration_minutes": 60,
    }
    data.update(overrides)
    return AppointmentCreate(**data)


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def clients():
    m = MagicMock()
    m.get_by_id.return_value = SimpleNamespace(id=1)
    return m


@pytest.fixture
def processes():
    m = MagicMock()
    m.get_by_id.return_value = SimpleNamespace(id=1)
    return m


@pytest.fixture
def service(repo, clients, processes):
    return AppointmentService(repo, clients, processes)


class TestCreate:
    def test_creates_with_valid_payload(self, service, repo):
        service.create_appointment(make_payload(), make_user(id=7))
        repo.create.assert_called_once()
        assert repo.create.call_args.kwargs["created_by"] == 7

    def test_rejects_unknown_client(self, service, clients):
        clients.get_by_id.return_value = None
        with pytest.raises(AppointmentClientNotFoundError):
            service.create_appointment(make_payload(client_id=99), make_user())

    def test_rejects_unknown_process(self, service, processes):
        processes.get_by_id.return_value = None
        with pytest.raises(AppointmentProcessNotFoundError):
            service.create_appointment(make_payload(process_id=99), make_user())


class TestGet:
    def test_raises_when_missing(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(AppointmentNotFoundError):
            service.get_appointment(1, make_user())

    def test_owner_can_access(self, service, repo):
        repo.get_by_id.return_value = SimpleNamespace(id=1, created_by=5)
        assert service.get_appointment(1, make_user(id=5)).id == 1

    def test_admin_can_access_other(self, service, repo):
        repo.get_by_id.return_value = SimpleNamespace(id=1, created_by=5)
        result = service.get_appointment(1, make_user(id=9, role=Role.ADMIN))
        assert result.id == 1

    def test_non_owner_non_admin_forbidden(self, service, repo):
        repo.get_by_id.return_value = SimpleNamespace(id=1, created_by=5)
        with pytest.raises(ForbiddenError):
            service.get_appointment(1, make_user(id=9))


class TestUpdate:
    def test_owner_updates(self, service, repo):
        repo.get_by_id.return_value = SimpleNamespace(id=1, created_by=5)
        service.update_appointment(1, AppointmentUpdate(title="novo"), make_user(id=5))
        repo.update.assert_called_once()

    def test_non_owner_forbidden(self, service, repo):
        repo.get_by_id.return_value = SimpleNamespace(id=1, created_by=5)
        with pytest.raises(ForbiddenError):
            service.update_appointment(1, AppointmentUpdate(title="x"), make_user(id=9))

    def test_validates_client_reference(self, service, repo, clients):
        repo.get_by_id.return_value = SimpleNamespace(id=1, created_by=5)
        clients.get_by_id.return_value = None
        with pytest.raises(AppointmentClientNotFoundError):
            service.update_appointment(
                1, AppointmentUpdate(client_id=99), make_user(id=5)
            )


class TestDelete:
    def test_owner_deletes(self, service, repo):
        appointment = SimpleNamespace(id=1, created_by=5)
        repo.get_by_id.return_value = appointment
        service.delete_appointment(1, make_user(id=5))
        repo.delete.assert_called_once_with(appointment)

    def test_non_owner_forbidden(self, service, repo):
        repo.get_by_id.return_value = SimpleNamespace(id=1, created_by=5)
        with pytest.raises(ForbiddenError):
            service.delete_appointment(1, make_user(id=9))


class TestList:
    def test_scopes_to_current_user(self, service, repo):
        repo.list.return_value = ([], 0)
        service.list_appointments(make_user(id=42), page=1, limit=20)
        assert repo.list.call_args.kwargs["created_by"] == 42


def make_google_sync(connected: bool = True, configured: bool = True) -> MagicMock:
    google = MagicMock()
    google.is_configured = configured
    google.get_status.return_value = SimpleNamespace(connected=connected)
    return google


class TestSyncAllToGoogle:
    def test_raises_when_not_configured(self, repo, clients, processes):
        google = make_google_sync(configured=False)
        service = AppointmentService(repo, clients, processes, google_sync=google)
        with pytest.raises(GoogleNotConfiguredError):
            service.sync_all_to_google(make_user())

    def test_raises_when_google_sync_absent(self, service):
        with pytest.raises(GoogleNotConfiguredError):
            service.sync_all_to_google(make_user())

    def test_raises_when_user_not_connected(self, repo, clients, processes):
        google = make_google_sync(connected=False)
        service = AppointmentService(repo, clients, processes, google_sync=google)
        with pytest.raises(GoogleNotConnectedError):
            service.sync_all_to_google(make_user())

    def test_syncs_unsynced_appointments(self, repo, clients, processes):
        google = make_google_sync()
        google.sync_appointment.side_effect = ["evt-1", "evt-2"]
        repo.list_unsynced_future.return_value = [
            SimpleNamespace(id=1),
            SimpleNamespace(id=2),
        ]
        service = AppointmentService(repo, clients, processes, google_sync=google)

        result = service.sync_all_to_google(make_user(id=5))

        assert (result.total, result.synced, result.failed) == (2, 2, 0)
        assert repo.update.call_count == 2
        assert repo.list_unsynced_future.call_args.args[0] == 5

    def test_counts_failures_without_updating(self, repo, clients, processes):
        google = make_google_sync()
        # segundo compromisso falha no Google -> sync_appointment devolve None
        google.sync_appointment.side_effect = ["evt-1", None]
        repo.list_unsynced_future.return_value = [
            SimpleNamespace(id=1),
            SimpleNamespace(id=2),
        ]
        service = AppointmentService(repo, clients, processes, google_sync=google)

        result = service.sync_all_to_google(make_user())

        assert (result.total, result.synced, result.failed) == (2, 1, 1)
        assert repo.update.call_count == 1

    def test_empty_when_nothing_to_sync(self, repo, clients, processes):
        google = make_google_sync()
        repo.list_unsynced_future.return_value = []
        service = AppointmentService(repo, clients, processes, google_sync=google)

        result = service.sync_all_to_google(make_user())

        assert (result.total, result.synced, result.failed) == (0, 0, 0)
