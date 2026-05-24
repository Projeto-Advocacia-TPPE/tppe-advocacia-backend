from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.modules.clients.model import Client
from app.modules.clients.schema import ClientCreate, ClientUpdate
from app.modules.clients.service import ClientService
from app.modules.users.model import User
from app.shared.exceptions import (
    ClientCnpjAlreadyExistsError,
    ClientCpfAlreadyExistsError,
    ClientHasActiveProcessesError,
    ClientNotFoundError,
)
from app.shared.types import Role


def make_client(**kwargs) -> Client:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "name": "João Silva",
        "email": "joao@example.com",
        "phone": None,
        "cpf": "12345678901",
        "cnpj": None,
        "address": None,
        "created_by": None,
        "updated_by": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    client = MagicMock(spec=Client)
    for key, value in defaults.items():
        setattr(client, key, value)
    return client


def make_user(user_id: int = 1) -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    return user


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    return ClientService(repo, process_repository=MagicMock(), audit=MagicMock())


@pytest.fixture
def anonymize_service(repo):
    process_repo = MagicMock()
    audit = MagicMock()
    svc = ClientService(repo, process_repository=process_repo, audit=audit)
    svc.process_repository = process_repo
    svc.audit = audit
    return svc


class TestCreateClient:
    def test_creates_when_cpf_not_duplicate(self, service, repo):
        repo.get_by_cpf.return_value = None
        client = make_client()
        repo.create.return_value = client
        payload = ClientCreate(name="João Silva", cpf="12345678901")
        user = make_user(user_id=5)

        result = service.create_client(payload, created_by=user)

        assert result is client
        repo.create.assert_called_once_with(
            name="João Silva",
            email=None,
            phone=None,
            cpf="12345678901",
            cnpj=None,
            address=None,
            created_by=5,
        )

    def test_creates_when_cnpj_not_duplicate(self, service, repo):
        repo.get_by_cnpj.return_value = None
        client = make_client(cpf=None, cnpj="12345678000195")
        repo.create.return_value = client
        payload = ClientCreate(name="Empresa X", cnpj="12345678000195")

        result = service.create_client(payload, created_by=make_user())

        assert result is client

    def test_raises_when_cpf_duplicate(self, service, repo):
        repo.get_by_cpf.return_value = make_client()
        payload = ClientCreate(name="João Silva", cpf="12345678901")

        with pytest.raises(ClientCpfAlreadyExistsError):
            service.create_client(payload, created_by=make_user())

        repo.create.assert_not_called()

    def test_raises_when_cnpj_duplicate(self, service, repo):
        repo.get_by_cnpj.return_value = make_client(cpf=None, cnpj="12345678000195")
        payload = ClientCreate(name="Empresa X", cnpj="12345678000195")

        with pytest.raises(ClientCnpjAlreadyExistsError):
            service.create_client(payload, created_by=make_user())

        repo.create.assert_not_called()


class TestGetClient:
    def test_returns_client_when_found(self, service, repo):
        client = make_client()
        repo.get_by_id.return_value = client

        result = service.get_client(1)

        assert result is client

    def test_raises_when_not_found(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ClientNotFoundError):
            service.get_client(99)


class TestListClients:
    def test_delegates_to_repository(self, service, repo):
        repo.list.return_value = ([], 0)

        result, total = service.list_clients()

        repo.list.assert_called_once_with(search=None, page=1, limit=20)
        assert result == []
        assert total == 0

    def test_passes_search_and_pagination(self, service, repo):
        repo.list.return_value = ([], 0)

        service.list_clients(search="João", page=2, limit=10)

        repo.list.assert_called_once_with(search="João", page=2, limit=10)


class TestUpdateClient:
    def test_updates_name(self, service, repo):
        client = make_client()
        updated = make_client(name="Maria Souza")
        repo.get_by_id.return_value = client
        repo.update.return_value = updated
        user = make_user(user_id=7)
        payload = ClientUpdate(name="Maria Souza")

        result = service.update_client(1, payload, updated_by=user)

        repo.update.assert_called_once_with(
            client, {"name": "Maria Souza", "updated_by": 7}
        )
        assert result is updated

    def test_raises_when_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        payload = ClientUpdate(name="Novo Nome")

        with pytest.raises(ClientNotFoundError):
            service.update_client(99, payload, updated_by=make_user())

    def test_skips_update_when_payload_empty(self, service, repo):
        client = make_client()
        repo.get_by_id.return_value = client
        payload = ClientUpdate()

        result = service.update_client(1, payload, updated_by=make_user())

        repo.update.assert_not_called()
        assert result is client

    def test_raises_when_new_cpf_already_exists(self, service, repo):
        client = make_client(cpf="11111111111")
        other = make_client(id=2, cpf="99999999999")
        repo.get_by_id.return_value = client
        repo.get_by_cpf.return_value = other
        payload = ClientUpdate(cpf="99999999999")

        with pytest.raises(ClientCpfAlreadyExistsError):
            service.update_client(1, payload, updated_by=make_user())

    def test_allows_update_with_same_cpf(self, service, repo):
        client = make_client(id=1, cpf="12345678901")
        repo.get_by_id.return_value = client
        repo.get_by_cpf.return_value = client
        repo.update.return_value = client
        payload = ClientUpdate(cpf="12345678901")

        result = service.update_client(1, payload, updated_by=make_user())

        repo.update.assert_called_once()
        assert result is client

    def test_raises_when_new_cnpj_already_exists(self, service, repo):
        client = make_client(cpf=None, cnpj="11111111000111")
        other = make_client(id=2, cpf=None, cnpj="99999999000199")
        repo.get_by_id.return_value = client
        repo.get_by_cnpj.return_value = other
        payload = ClientUpdate(cnpj="99999999000199")

        with pytest.raises(ClientCnpjAlreadyExistsError):
            service.update_client(1, payload, updated_by=make_user())

    def test_sets_updated_by_on_update(self, service, repo):
        client = make_client()
        repo.get_by_id.return_value = client
        repo.update.return_value = client
        user = make_user(user_id=42)
        payload = ClientUpdate(name="Novo Nome")

        service.update_client(1, payload, updated_by=user)

        call_data = repo.update.call_args[0][1]
        assert call_data["updated_by"] == 42

    def test_nullifies_cnpj_when_cpf_updated(self, service, repo):
        client = make_client(cpf=None, cnpj="11111111000111")
        repo.get_by_id.return_value = client
        repo.get_by_cpf.return_value = None
        repo.update.return_value = client
        payload = ClientUpdate(cpf="12345678901")

        service.update_client(1, payload, updated_by=make_user())

        call_data = repo.update.call_args[0][1]
        assert call_data["cpf"] == "12345678901"
        assert call_data["cnpj"] is None

    def test_nullifies_cpf_when_cnpj_updated(self, service, repo):
        client = make_client(cpf="12345678901", cnpj=None)
        repo.get_by_id.return_value = client
        repo.get_by_cnpj.return_value = None
        repo.update.return_value = client
        payload = ClientUpdate(cnpj="11111111000111")

        service.update_client(1, payload, updated_by=make_user())

        call_data = repo.update.call_args[0][1]
        assert call_data["cnpj"] == "11111111000111"
        assert call_data["cpf"] is None


class TestGetClientVisibility:
    def test_non_admin_passes_include_deleted_false(self, service, repo):
        client = make_client()
        repo.get_by_id.return_value = client
        requester = MagicMock(spec=User)
        requester.role = Role.USER

        service.get_client(1, requester=requester)

        repo.get_by_id.assert_called_once_with(1, include_deleted=False)

    def test_admin_passes_include_deleted_true(self, service, repo):
        client = make_client()
        repo.get_by_id.return_value = client
        requester = MagicMock(spec=User)
        requester.role = Role.ADMIN

        service.get_client(1, requester=requester)

        repo.get_by_id.assert_called_once_with(1, include_deleted=True)

    def test_without_requester_excludes_deleted(self, service, repo):
        client = make_client()
        repo.get_by_id.return_value = client

        service.get_client(1)

        repo.get_by_id.assert_called_once_with(1, include_deleted=False)


class TestAnonymize:
    def test_anonymizes_when_no_active_processes(self, anonymize_service, repo):
        client = make_client(name="João Silva")
        repo.get_by_id.return_value = client
        anonymize_service.process_repository.count_active_or_suspended_by_client.return_value = 0
        repo.db = MagicMock()
        performed_by = make_user(user_id=7)

        result = anonymize_service.anonymize(1, performed_by=performed_by)

        repo.anonymize.assert_called_once()
        anonymize_service.audit.log_client_anonymized.assert_called_once_with(
            client_id=1,
            client_name="João Silva",
            performed_by=performed_by,
        )
        repo.db.commit.assert_called_once()
        repo.db.refresh.assert_called_once_with(client)
        assert result is client

    def test_raises_not_found_when_client_missing(self, anonymize_service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ClientNotFoundError):
            anonymize_service.anonymize(99, performed_by=make_user())

        repo.anonymize.assert_not_called()
        anonymize_service.audit.log_client_anonymized.assert_not_called()

    def test_raises_when_has_active_processes(self, anonymize_service, repo):
        client = make_client()
        repo.get_by_id.return_value = client
        anonymize_service.process_repository.count_active_or_suspended_by_client.return_value = 1

        with pytest.raises(ClientHasActiveProcessesError):
            anonymize_service.anonymize(1, performed_by=make_user())

        repo.anonymize.assert_not_called()
        anonymize_service.audit.log_client_anonymized.assert_not_called()

    def test_rollback_on_failure(self, anonymize_service, repo):
        client = make_client()
        repo.get_by_id.return_value = client
        anonymize_service.process_repository.count_active_or_suspended_by_client.return_value = 0
        repo.db = MagicMock()
        repo.anonymize.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            anonymize_service.anonymize(1, performed_by=make_user())

        repo.db.rollback.assert_called_once()
        repo.db.commit.assert_not_called()
