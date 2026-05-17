from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.processes.model import MovementSource, Process, ProcessStatus
from app.modules.processes.schema import MovementCreate, ProcessCreate
from app.modules.processes.service import ProcessService
from app.modules.users.model import User
from app.shared.exceptions import (
    ClientNotFoundError,
    ClientNotFoundForProcessError,
    ProcessNotFoundError,
    ProcessNumberAlreadyExistsError,
)


def make_process(**kwargs) -> Process:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "number": "12345678920248260100",
        "client_id": 1,
        "court": "TJSP",
        "action_type": "Ação Cível",
        "opposing_party": None,
        "status": ProcessStatus.ATIVO,
        "created_by": 5,
        "updated_by": 5,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    process = MagicMock(spec=Process)
    for key, value in defaults.items():
        setattr(process, key, value)
    return process


def make_user(user_id: int = 5) -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    return user


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def client_repo():
    return MagicMock()


@pytest.fixture
def service(repo, client_repo):
    svc = ProcessService.__new__(ProcessService)
    svc.repository = repo
    svc.client_repository = client_repo
    return svc


class TestCreateProcess:
    def _payload(self) -> ProcessCreate:
        return ProcessCreate(
            number="1234567-89.2024.8.26.0100",
            client_id=1,
            court="TJSP",
            action_type="Ação Cível",
        )

    def test_creates_when_client_exists(self, service, repo, client_repo):
        client_repo.get_by_id.return_value = MagicMock()
        process = make_process()
        repo.create.return_value = process

        result = service.create_process(self._payload(), created_by=make_user(5))

        assert result is process
        repo.create.assert_called_once_with(
            number="12345678920248260100",
            client_id=1,
            court="TJSP",
            action_type="Ação Cível",
            opposing_party=None,
            created_by=5,
        )

    def test_creates_without_client(self, service, repo, client_repo):
        process = make_process(client_id=None)
        repo.create.return_value = process
        payload = ProcessCreate(
            number="1234567-89.2024.8.26.0100",
            court="TJSP",
            action_type="Ação Cível",
        )

        result = service.create_process(payload, created_by=make_user(5))

        assert result is process
        client_repo.get_by_id.assert_not_called()
        repo.create.assert_called_once_with(
            number="12345678920248260100",
            client_id=None,
            court="TJSP",
            action_type="Ação Cível",
            opposing_party=None,
            created_by=5,
        )

    def test_raises_when_client_not_found(self, service, repo, client_repo):
        client_repo.get_by_id.return_value = None

        with pytest.raises(ClientNotFoundForProcessError):
            service.create_process(self._payload(), created_by=make_user())

        repo.create.assert_not_called()

    def test_raises_when_number_duplicate(self, service, repo, client_repo):
        client_repo.get_by_id.return_value = MagicMock()
        repo.create.side_effect = IntegrityError("stmt", {}, Exception("dup"))
        repo.db = MagicMock()

        with pytest.raises(ProcessNumberAlreadyExistsError):
            service.create_process(self._payload(), created_by=make_user())

        repo.db.rollback.assert_called_once()


class TestGetProcess:
    def test_returns_when_found(self, service, repo):
        process = make_process()
        repo.get_by_id.return_value = process

        assert service.get_process(1) is process

    def test_raises_when_not_found(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ProcessNotFoundError):
            service.get_process(99)


class TestListProcesses:
    def test_delegates_to_repository_defaults(self, service, repo):
        repo.list.return_value = ([], 0)

        result, total = service.list_processes()

        repo.list.assert_called_once_with(
            client_id=None, status=None, search=None, page=1, limit=20
        )
        assert result == []
        assert total == 0

    def test_passes_filters(self, service, repo):
        repo.list.return_value = ([], 0)

        service.list_processes(
            client_id=5, status=ProcessStatus.SUSPENSO, search="cível", page=2, limit=10
        )

        repo.list.assert_called_once_with(
            client_id=5,
            status=ProcessStatus.SUSPENSO,
            search="cível",
            page=2,
            limit=10,
        )


class TestListByClient:
    def test_returns_list_when_client_exists(self, service, repo, client_repo):
        client_repo.get_by_id.return_value = MagicMock()
        repo.list_by_client.return_value = ([], 0)

        result, total = service.list_by_client(1)

        repo.list_by_client.assert_called_once_with(client_id=1, page=1, limit=20)
        assert result == []
        assert total == 0

    def test_raises_when_client_not_found(self, service, repo, client_repo):
        client_repo.get_by_id.return_value = None

        with pytest.raises(ClientNotFoundError):
            service.list_by_client(99)

        repo.list_by_client.assert_not_called()


class TestCreateMovement:
    def test_creates_with_source_manual_and_now_default(self, service, repo):
        process = make_process()
        repo.get_by_id.return_value = process
        repo.create_movement.return_value = MagicMock()
        payload = MovementCreate(title="Audiência marcada")

        before = datetime.now(timezone.utc)
        service.create_movement(1, payload, created_by=make_user(7))
        after = datetime.now(timezone.utc)

        repo.create_movement.assert_called_once()
        kwargs = repo.create_movement.call_args.kwargs
        assert kwargs["process_id"] == 1
        assert kwargs["title"] == "Audiência marcada"
        assert kwargs["description"] is None
        assert kwargs["source"] == MovementSource.MANUAL
        assert kwargs["created_by"] == 7
        assert before <= kwargs["occurred_at"] <= after

    def test_uses_provided_occurred_at(self, service, repo):
        repo.get_by_id.return_value = make_process()
        repo.create_movement.return_value = MagicMock()
        past = datetime.now(timezone.utc) - timedelta(days=2)
        payload = MovementCreate(title="Petição protocolada", occurred_at=past)

        service.create_movement(1, payload, created_by=make_user(7))

        assert repo.create_movement.call_args.kwargs["occurred_at"] == past

    def test_raises_when_process_missing(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ProcessNotFoundError):
            service.create_movement(
                99, MovementCreate(title="X"), created_by=make_user()
            )

        repo.create_movement.assert_not_called()


class TestListMovements:
    def test_validates_process_and_delegates(self, service, repo):
        repo.get_by_id.return_value = make_process()
        repo.list_movements.return_value = ([], 0)

        result, total = service.list_movements(1)

        repo.list_movements.assert_called_once_with(
            process_id=1,
            source=None,
            date_from=None,
            date_to=None,
            page=1,
            limit=20,
        )
        assert result == []
        assert total == 0

    def test_passes_filters(self, service, repo):
        repo.get_by_id.return_value = make_process()
        repo.list_movements.return_value = ([], 0)
        date_from = datetime.now(timezone.utc) - timedelta(days=10)
        date_to = datetime.now(timezone.utc)

        service.list_movements(
            1,
            source=MovementSource.SYSTEM,
            date_from=date_from,
            date_to=date_to,
            page=2,
            limit=5,
        )

        repo.list_movements.assert_called_once_with(
            process_id=1,
            source=MovementSource.SYSTEM,
            date_from=date_from,
            date_to=date_to,
            page=2,
            limit=5,
        )

    def test_raises_when_process_missing(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ProcessNotFoundError):
            service.list_movements(99)

        repo.list_movements.assert_not_called()
