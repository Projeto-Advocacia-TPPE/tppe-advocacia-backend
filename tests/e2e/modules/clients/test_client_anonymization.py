import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.audit_logs.model import AuditAction, AuditLog
from app.modules.clients.model import Client, ClientNote
from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import Process, ProcessStatus
from app.modules.processes.repository import ProcessRepository

CLIENTS_URL = "/api/v1/clients"


@pytest.fixture
def created_client_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(AuditLog).where(AuditLog.target_client_id.in_(ids)))
    db_session.execute(delete(ClientNote).where(ClientNote.client_id.in_(ids)))
    db_session.execute(delete(Process).where(Process.client_id.in_(ids)))
    db_session.execute(delete(Client).where(Client.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def anon_client(db_session: Session, created_client_ids):
    c = ClientRepository(db_session).create(
        name="Carlos Anonimo",
        email="carlos@example.com",
        phone="11999999999",
        cpf="88877766651",
        address="Rua A, 1",
    )
    db_session.commit()
    created_client_ids.append(c.id)
    return c


class TestDeleteClientAuth:
    def test_returns_401_without_token(self, client, anon_client):
        response = client.delete(f"{CLIENTS_URL}/{anon_client.id}?confirm=true")
        assert response.status_code == 401

    def test_returns_403_for_non_admin(self, client, user_headers, anon_client):
        response = client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=user_headers,
        )
        assert response.status_code == 403


class TestDeleteClientConfirmation:
    def test_returns_400_without_confirm(self, client, admin_headers, anon_client):
        response = client.delete(
            f"{CLIENTS_URL}/{anon_client.id}",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "CONFIRMATION_REQUIRED"

    def test_returns_400_with_confirm_false(self, client, admin_headers, anon_client):
        response = client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=false",
            headers=admin_headers,
        )
        assert response.status_code == 400


class TestDeleteClientNotFound:
    def test_returns_404_when_missing(self, client, admin_headers):
        response = client.delete(
            f"{CLIENTS_URL}/9999999?confirm=true",
            headers=admin_headers,
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CLIENT_NOT_FOUND"


class TestDeleteClientActiveProcesses:
    def test_returns_409_when_has_active_process(
        self, client, admin_headers, db_session, anon_client, created_client_ids
    ):
        ProcessRepository(db_session).create(
            number="11111111111111111111",
            court="TJSP",
            action_type="Ação Cível",
            client_id=anon_client.id,
            created_by=None,
        )

        response = client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CLIENT_HAS_ACTIVE_PROCESSES"

    def test_returns_409_when_has_suspended_process(
        self, client, admin_headers, db_session, anon_client
    ):
        process_repo = ProcessRepository(db_session)
        process = process_repo.create(
            number="22222222222222222222",
            court="TJSP",
            action_type="Ação Cível",
            client_id=anon_client.id,
            created_by=None,
        )
        process_repo.update_status_no_commit(
            process, ProcessStatus.SUSPENSO, updated_by=None
        )
        db_session.commit()

        response = client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        assert response.status_code == 409

    def test_succeeds_with_only_archived_processes(
        self, client, admin_headers, db_session, anon_client
    ):
        process_repo = ProcessRepository(db_session)
        process = process_repo.create(
            number="33333333333333333333",
            court="TJSP",
            action_type="Ação Cível",
            client_id=anon_client.id,
            created_by=None,
        )
        process_repo.update_status_no_commit(
            process, ProcessStatus.ARQUIVADO, updated_by=None
        )
        db_session.commit()

        response = client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        assert response.status_code == 204


class TestDeleteClientSuccessfulFlow:
    def test_anonymizes_client_data(
        self, client, admin_headers, db_session, anon_client
    ):
        response = client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )
        assert response.status_code == 204

        db_session.expire_all()
        stored = db_session.scalars(
            select(Client).where(Client.id == anon_client.id)
        ).first()
        assert stored.name == "[ANONIMIZADO]"
        assert stored.email is None
        assert stored.phone is None
        assert stored.cpf is None
        assert stored.cnpj is None
        assert stored.address is None
        assert stored.deleted_at is not None

    def test_anonymizes_notes(
        self, client, admin_headers, admin_user, db_session, anon_client
    ):
        ClientRepository(db_session).create_note(
            client_id=anon_client.id,
            created_by=admin_user["id"],
            content="conteudo sensivel",
        )
        db_session.commit()

        client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        db_session.expire_all()
        notes = db_session.scalars(
            select(ClientNote).where(ClientNote.client_id == anon_client.id)
        ).all()
        assert len(notes) == 1
        assert notes[0].content == "[ANONIMIZADO]"
        assert notes[0].deleted_at is not None

    def test_creates_audit_log(self, client, admin_headers, db_session, anon_client):
        original_name = anon_client.name

        client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        log = db_session.scalars(
            select(AuditLog)
            .where(AuditLog.target_client_id == anon_client.id)
            .where(AuditLog.action == AuditAction.CLIENT_ANONYMIZED)
        ).first()
        assert log is not None
        assert log.target_client_name == original_name
        assert log.performed_by_id is not None


class TestVisibilityAfterAnonymization:
    def test_not_listed_in_get_clients_for_admin(
        self, client, admin_headers, anon_client
    ):
        client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        response = client.get(CLIENTS_URL, headers=admin_headers)
        ids = [c["id"] for c in response.json()["data"]]
        assert anon_client.id not in ids

    def test_search_does_not_find_anonymized(self, client, admin_headers, anon_client):
        original_cpf = anon_client.cpf
        client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        response = client.get(
            f"{CLIENTS_URL}?search={original_cpf}", headers=admin_headers
        )
        ids = [c["id"] for c in response.json()["data"]]
        assert anon_client.id not in ids

    def test_get_by_id_returns_404_for_non_admin(
        self, client, admin_headers, user_headers, anon_client
    ):
        client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        response = client.get(f"{CLIENTS_URL}/{anon_client.id}", headers=user_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CLIENT_NOT_FOUND"

    def test_get_by_id_returns_200_for_admin(self, client, admin_headers, anon_client):
        client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        response = client.get(f"{CLIENTS_URL}/{anon_client.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "[ANONIMIZADO]"
        assert data["email"] is None
        assert data["cpf"] is None
        assert data["deleted_at"] is not None

    def test_process_shows_anonymized_client_name(
        self, client, admin_headers, db_session, anon_client
    ):
        process = ProcessRepository(db_session).create(
            number="44444444444444444444",
            court="TJSP",
            action_type="Ação Cível",
            client_id=anon_client.id,
            created_by=None,
        )
        ProcessRepository(db_session).update_status_no_commit(
            process, ProcessStatus.ARQUIVADO, updated_by=None
        )
        db_session.commit()

        client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        response = client.get(f"/api/v1/processes/{process.id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["data"]["client_name"] == "[ANONIMIZADO]"


class TestCpfReuseAfterAnonymization:
    def test_can_create_new_client_with_same_cpf(
        self, client, admin_headers, user_headers, anon_client, created_client_ids
    ):
        original_cpf = anon_client.cpf

        client.delete(
            f"{CLIENTS_URL}/{anon_client.id}?confirm=true",
            headers=admin_headers,
        )

        response = client.post(
            CLIENTS_URL,
            json={"name": "Novo Cliente Reuso", "cpf": original_cpf},
            headers=user_headers,
        )

        assert response.status_code == 201
        created_client_ids.append(response.json()["data"]["id"])
