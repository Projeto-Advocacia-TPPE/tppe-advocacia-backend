from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.clients.model import Client, ClientNote
from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import (
    MovementSource,
    Process,
    ProcessMovement,
    ProcessNote,
)
from app.modules.processes.repository import ProcessRepository


def _url(client_id: int) -> str:
    return f"/api/v1/clients/{client_id}/timeline"


@pytest.fixture
def created_client_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(Client).where(Client.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def created_process_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(ProcessNote).where(ProcessNote.process_id.in_(ids)))
    db_session.execute(
        delete(ProcessMovement).where(ProcessMovement.process_id.in_(ids))
    )
    db_session.execute(delete(Process).where(Process.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def created_note_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(ClientNote).where(ClientNote.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def empty_client(db_session, created_client_ids):
    c = ClientRepository(db_session).create(name="Vazio TL", cpf="99988877766")
    db_session.commit()
    created_client_ids.append(c.id)
    return c


@pytest.fixture
def populated_client(
    db_session,
    active_user,
    created_client_ids,
    created_process_ids,
    created_note_ids,
):
    crepo = ClientRepository(db_session)
    prepo = ProcessRepository(db_session)

    client = crepo.create(name="Populado TL", cpf="88877766655")
    db_session.commit()
    created_client_ids.append(client.id)

    for i in range(2):
        n = crepo.create_note(
            client_id=client.id,
            created_by=active_user["id"],
            content=f"nota {i}",
        )
        created_note_ids.append(n.id)
    db_session.commit()

    base = datetime.now(timezone.utc) - timedelta(days=10)
    processes_info = []
    for i in range(2):
        p = prepo.create(
            number=f"1234567892024826680{i}",
            client_id=client.id,
            court="TJSP",
            action_type=f"Ação {i}",
        )
        created_process_ids.append(p.id)
        last = prepo.create_movement(
            process_id=p.id,
            title=f"Movimentação P{i}",
            occurred_at=base + timedelta(days=i + 1),
            source=MovementSource.MANUAL,
            created_by=active_user["id"],
        )
        processes_info.append((p, last))
    db_session.commit()

    return {"client": client, "processes": processes_info}


class TestClientTimeline:
    def test_returns_401_without_token(self, client, empty_client):
        response = client.get(_url(empty_client.id))

        assert response.status_code == 401

    def test_returns_404_when_client_missing(self, client, user_headers):
        response = client.get(_url(999999), headers=user_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CLIENT_NOT_FOUND"

    def test_empty_client_returns_all_sections_empty(
        self, client, user_headers, empty_client
    ):
        response = client.get(_url(empty_client.id), headers=user_headers)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["client"]["id"] == empty_client.id
        assert data["notes"] == []
        assert data["processes"] == []
        assert data["recent_activity"] == []

    def test_populated_client_returns_full_payload(
        self, client, user_headers, populated_client
    ):
        client_id = populated_client["client"].id

        response = client.get(_url(client_id), headers=user_headers)

        assert response.status_code == 200
        data = response.json()["data"]

        assert data["client"]["id"] == client_id
        assert len(data["notes"]) == 2

        assert len(data["processes"]) == 2
        for ps in data["processes"]:
            assert ps["last_movement"] is not None
            assert ps["last_movement"]["title"].startswith("Movimentação P")

        kinds = {item["kind"] for item in data["recent_activity"]}
        assert kinds == {"movement", "client_note"}

    def test_activity_limit_truncates_feed(
        self, client, user_headers, populated_client
    ):
        client_id = populated_client["client"].id

        response = client.get(
            _url(client_id) + "?activity_limit=1", headers=user_headers
        )

        assert response.status_code == 200
        assert len(response.json()["data"]["recent_activity"]) == 1

    def test_returns_422_when_limit_zero(self, client, user_headers, empty_client):
        response = client.get(
            _url(empty_client.id) + "?notes_limit=0", headers=user_headers
        )

        assert response.status_code == 422

    def test_returns_422_when_limit_too_high(self, client, user_headers, empty_client):
        response = client.get(
            _url(empty_client.id) + "?activity_limit=51", headers=user_headers
        )

        assert response.status_code == 422
