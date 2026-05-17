from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import MovementSource, Process, ProcessMovement
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
        name="Cliente Mov E2E", cpf="33344455566"
    )
    created_client_ids.append(client.id)
    process = ProcessRepository(db_session).create(
        number="12345678920248262200",
        client_id=client.id,
        court="TJSP",
        action_type="Ação Cível",
    )
    created_process_ids.append(process.id)
    return process


def _url(process_id: int) -> str:
    return f"/api/v1/processes/{process_id}/movements"


class TestCreateMovement:
    def test_returns_401_without_token(self, client, process_fixture):
        response = client.post(_url(process_fixture.id), json={"title": "X"})

        assert response.status_code == 401

    def test_creates_with_defaults(
        self,
        client,
        user_headers,
        active_user,
        process_fixture,
        created_movement_ids,
    ):
        response = client.post(
            _url(process_fixture.id),
            json={"title": "Audiência marcada"},
            headers=user_headers,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["process_id"] == process_fixture.id
        assert data["title"] == "Audiência marcada"
        assert data["source"] == "MANUAL"
        assert data["created_by"] == active_user["id"]
        assert data["created_by_name"] == "Active User"
        assert data["occurred_at"] is not None
        created_movement_ids.append(data["id"])

    def test_returns_404_when_process_missing(self, client, user_headers):
        response = client.post(_url(999999), json={"title": "X"}, headers=user_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROCESS_NOT_FOUND"

    def test_returns_422_empty_title(self, client, user_headers, process_fixture):
        response = client.post(
            _url(process_fixture.id), json={"title": ""}, headers=user_headers
        )

        assert response.status_code == 422

    def test_returns_422_description_too_long(
        self, client, user_headers, process_fixture
    ):
        response = client.post(
            _url(process_fixture.id),
            json={"title": "ok", "description": "A" * 5001},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_returns_422_future_occurred_at(
        self, client, user_headers, process_fixture
    ):
        future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        response = client.post(
            _url(process_fixture.id),
            json={"title": "ok", "occurred_at": future},
            headers=user_headers,
        )

        assert response.status_code == 422


class TestListMovements:
    def test_returns_401_without_token(self, client, process_fixture):
        response = client.get(_url(process_fixture.id))

        assert response.status_code == 401

    def test_returns_404_when_process_missing(self, client, user_headers):
        response = client.get(_url(999999), headers=user_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROCESS_NOT_FOUND"

    def test_lists_ordered_desc(
        self,
        client,
        user_headers,
        process_fixture,
        db_session,
        created_movement_ids,
    ):
        repo = ProcessRepository(db_session)
        base = datetime.now(timezone.utc) - timedelta(days=5)
        older = repo.create_movement(
            process_id=process_fixture.id,
            title="Older",
            occurred_at=base,
            source=MovementSource.MANUAL,
        )
        newer = repo.create_movement(
            process_id=process_fixture.id,
            title="Newer",
            occurred_at=base + timedelta(days=2),
            source=MovementSource.MANUAL,
        )
        created_movement_ids.extend([older.id, newer.id])

        response = client.get(_url(process_fixture.id), headers=user_headers)

        assert response.status_code == 200
        body = response.json()
        ids = [m["id"] for m in body["data"]]
        assert ids.index(newer.id) < ids.index(older.id)
        assert body["meta"]["total"] >= 2

    def test_filter_by_source(
        self,
        client,
        user_headers,
        process_fixture,
        db_session,
        created_movement_ids,
    ):
        repo = ProcessRepository(db_session)
        manual = repo.create_movement(
            process_id=process_fixture.id,
            title="M",
            occurred_at=datetime.now(timezone.utc),
            source=MovementSource.MANUAL,
        )
        system = repo.create_movement(
            process_id=process_fixture.id,
            title="S",
            occurred_at=datetime.now(timezone.utc),
            source=MovementSource.SYSTEM,
        )
        created_movement_ids.extend([manual.id, system.id])

        response = client.get(
            f"{_url(process_fixture.id)}?source=SYSTEM", headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert all(m["source"] == "SYSTEM" for m in data)
        assert any(m["id"] == system.id for m in data)
        assert not any(m["id"] == manual.id for m in data)


class TestImmutability:
    def test_patch_returns_405(self, client, user_headers, process_fixture):
        response = client.patch(
            _url(process_fixture.id),
            json={"title": "novo"},
            headers=user_headers,
        )

        assert response.status_code == 405

    def test_delete_returns_405(self, client, user_headers, process_fixture):
        response = client.delete(_url(process_fixture.id), headers=user_headers)

        assert response.status_code == 405
