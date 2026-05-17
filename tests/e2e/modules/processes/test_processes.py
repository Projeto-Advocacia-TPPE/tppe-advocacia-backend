import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import Process
from app.modules.processes.repository import ProcessRepository

PROCESSES_URL = "/api/v1/processes"


@pytest.fixture
def created_process_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(Process).where(Process.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def created_client_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(Client).where(Client.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def client_fixture(db_session: Session, created_client_ids):
    c = ClientRepository(db_session).create(
        name="Cliente E2E Process", cpf="22233344455"
    )
    created_client_ids.append(c.id)
    return c


@pytest.fixture
def other_client_fixture(db_session: Session, created_client_ids):
    c = ClientRepository(db_session).create(name="Outro Cliente E2E", cpf="66677788899")
    created_client_ids.append(c.id)
    return c


class TestCreateProcess:
    def test_returns_401_without_token(self, client, client_fixture):
        response = client.post(
            PROCESSES_URL,
            json={
                "number": "1234567-89.2024.8.26.1100",
                "client_id": client_fixture.id,
                "court": "TJSP",
                "action_type": "Ação Cível",
            },
        )

        assert response.status_code == 401

    def test_creates_process(
        self, client, user_headers, active_user, client_fixture, created_process_ids
    ):
        response = client.post(
            PROCESSES_URL,
            json={
                "number": "1234567-89.2024.8.26.1101",
                "client_id": client_fixture.id,
                "court": "TJSP",
                "action_type": "Ação Cível",
            },
            headers=user_headers,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["number"] == "1234567-89.2024.8.26.1101"
        assert data["client_id"] == client_fixture.id
        assert data["client_name"] == client_fixture.name
        assert data["status"] == "ATIVO"
        assert data["created_by"] == active_user["id"]
        created_process_ids.append(data["id"])

    def test_normalizes_digits_only_number(
        self, client, user_headers, client_fixture, created_process_ids
    ):
        response = client.post(
            PROCESSES_URL,
            json={
                "number": "12345678920248261102",
                "client_id": client_fixture.id,
                "court": "TJSP",
                "action_type": "Ação Cível",
            },
            headers=user_headers,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["number"] == "1234567-89.2024.8.26.1102"
        created_process_ids.append(data["id"])

    def test_returns_422_for_invalid_number(self, client, user_headers, client_fixture):
        response = client.post(
            PROCESSES_URL,
            json={
                "number": "abc",
                "client_id": client_fixture.id,
                "court": "TJSP",
                "action_type": "Ação Cível",
            },
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_returns_422_when_client_not_exists(self, client, user_headers):
        response = client.post(
            PROCESSES_URL,
            json={
                "number": "1234567-89.2024.8.26.1103",
                "client_id": 999999,
                "court": "TJSP",
                "action_type": "Ação Cível",
            },
            headers=user_headers,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "CLIENT_NOT_FOUND_FOR_PROCESS"

    def test_returns_409_on_duplicate_number(
        self,
        client,
        user_headers,
        client_fixture,
        db_session,
        created_process_ids,
    ):
        existing = ProcessRepository(db_session).create(
            number="12345678920248261104",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        created_process_ids.append(existing.id)

        response = client.post(
            PROCESSES_URL,
            json={
                "number": "1234567-89.2024.8.26.1104",
                "client_id": client_fixture.id,
                "court": "TJSP",
                "action_type": "Ação Cível",
            },
            headers=user_headers,
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PROCESS_NUMBER_ALREADY_EXISTS"


class TestGetProcess:
    def test_returns_401_without_token(self, client):
        response = client.get(f"{PROCESSES_URL}/1")

        assert response.status_code == 401

    def test_returns_process(
        self,
        client,
        user_headers,
        client_fixture,
        db_session,
        created_process_ids,
    ):
        created = ProcessRepository(db_session).create(
            number="12345678920248261200",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        created_process_ids.append(created.id)

        response = client.get(f"{PROCESSES_URL}/{created.id}", headers=user_headers)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == created.id
        assert data["client_name"] == client_fixture.name

    def test_returns_404_when_not_found(self, client, user_headers):
        response = client.get(f"{PROCESSES_URL}/999999", headers=user_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROCESS_NOT_FOUND"


class TestListProcesses:
    def test_returns_401_without_token(self, client):
        response = client.get(PROCESSES_URL)

        assert response.status_code == 401

    def test_returns_paginated_structure(self, client, user_headers):
        response = client.get(PROCESSES_URL, headers=user_headers)
        body = response.json()

        assert body["success"] is True
        assert "data" in body
        assert "meta" in body

    def test_filter_by_client_id(
        self,
        client,
        user_headers,
        client_fixture,
        db_session,
        created_process_ids,
    ):
        created = ProcessRepository(db_session).create(
            number="12345678920248261300",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        created_process_ids.append(created.id)

        response = client.get(
            f"{PROCESSES_URL}?client_id={client_fixture.id}", headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert all(p["client_id"] == client_fixture.id for p in data)


class TestListProcessesByClient:
    def test_returns_401_without_token(self, client, client_fixture):
        response = client.get(f"/api/v1/clients/{client_fixture.id}/processes")

        assert response.status_code == 401

    def test_returns_404_when_client_missing(self, client, user_headers):
        response = client.get("/api/v1/clients/999999/processes", headers=user_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CLIENT_NOT_FOUND"

    def test_returns_processes_of_client(
        self,
        client,
        user_headers,
        client_fixture,
        other_client_fixture,
        db_session,
        created_process_ids,
    ):
        repo = ProcessRepository(db_session)
        owned = repo.create(
            number="12345678920248261400",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        other = repo.create(
            number="12345678920248261401",
            client_id=other_client_fixture.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        created_process_ids.extend([owned.id, other.id])

        response = client.get(
            f"/api/v1/clients/{client_fixture.id}/processes", headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == owned.id
