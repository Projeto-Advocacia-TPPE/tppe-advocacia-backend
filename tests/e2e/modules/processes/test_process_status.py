import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import Process, ProcessMovement
from app.modules.processes.repository import ProcessRepository


@pytest.fixture
def created_movement_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(ProcessMovement).where(ProcessMovement.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def created_process_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(
        delete(ProcessMovement).where(ProcessMovement.process_id.in_(ids))
    )
    db_session.execute(delete(Process).where(Process.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def created_client_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(Client).where(Client.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def process_fixture(db_session: Session, created_client_ids, created_process_ids):
    client = ClientRepository(db_session).create(
        name="Cliente Status E2E", cpf="44455566677"
    )
    created_client_ids.append(client.id)
    process = ProcessRepository(db_session).create(
        number="12345678920248263300",
        client_id=client.id,
        court="TJSP",
        action_type="Ação Cível",
    )
    created_process_ids.append(process.id)
    return process


def _url(process_id: int) -> str:
    return f"/api/v1/processes/{process_id}/status"


class TestChangeStatus:
    def test_returns_401_without_token(self, client, process_fixture):
        response = client.patch(_url(process_fixture.id), json={"status": "SUSPENSO"})

        assert response.status_code == 401

    def test_returns_404_when_process_missing(self, client, user_headers):
        response = client.patch(
            _url(999999), json={"status": "SUSPENSO"}, headers=user_headers
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROCESS_NOT_FOUND"

    def test_changes_status_and_creates_system_movement(
        self,
        client,
        user_headers,
        active_user,
        process_fixture,
    ):
        response = client.patch(
            _url(process_fixture.id),
            json={"status": "SUSPENSO", "reason": "Acordo em andamento"},
            headers=user_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "SUSPENSO"
        assert data["updated_by"] == active_user["id"]
        movement_id = data["last_status_change_movement_id"]
        assert isinstance(movement_id, int)

        listing = client.get(
            f"/api/v1/processes/{process_fixture.id}/movements?source=SYSTEM",
            headers=user_headers,
        )
        assert listing.status_code == 200
        movements = listing.json()["data"]
        match = next((m for m in movements if m["id"] == movement_id), None)
        assert match is not None
        assert match["title"] == "Status alterado: ATIVO → SUSPENSO"
        assert match["description"] == "Acordo em andamento"
        assert match["source"] == "SYSTEM"
        assert match["created_by"] == active_user["id"]

    def test_returns_409_when_same_status(self, client, user_headers, process_fixture):
        response = client.patch(
            _url(process_fixture.id),
            json={"status": "ATIVO"},
            headers=user_headers,
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PROCESS_STATUS_UNCHANGED"

    def test_returns_422_for_invalid_status(
        self, client, user_headers, process_fixture
    ):
        response = client.patch(
            _url(process_fixture.id),
            json={"status": "INVALIDO"},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_returns_422_when_reason_too_long(
        self, client, user_headers, process_fixture
    ):
        response = client.patch(
            _url(process_fixture.id),
            json={"status": "SUSPENSO", "reason": "x" * 501},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_reason_optional_persists_null_description(
        self, client, user_headers, process_fixture
    ):
        response = client.patch(
            _url(process_fixture.id),
            json={"status": "ARQUIVADO"},
            headers=user_headers,
        )

        assert response.status_code == 200
        movement_id = response.json()["data"]["last_status_change_movement_id"]

        listing = client.get(
            f"/api/v1/processes/{process_fixture.id}/movements",
            headers=user_headers,
        )
        movements = listing.json()["data"]
        match = next((m for m in movements if m["id"] == movement_id), None)
        assert match is not None
        assert match["description"] is None
