import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import Process, ProcessNote
from app.modules.processes.repository import ProcessRepository


@pytest.fixture
def created_note_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(ProcessNote).where(ProcessNote.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def created_process_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(ProcessNote).where(ProcessNote.process_id.in_(ids)))
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
        name="Cliente Notes E2E", cpf="55566677700"
    )
    created_client_ids.append(client.id)
    process = ProcessRepository(db_session).create(
        number="12345678920248265500",
        client_id=client.id,
        court="TJSP",
        action_type="Ação Cível",
    )
    created_process_ids.append(process.id)
    return process


def _url(process_id: int) -> str:
    return f"/api/v1/processes/{process_id}/notes"


class TestCreateNote:
    def test_returns_401_without_token(self, client, process_fixture):
        response = client.post(_url(process_fixture.id), json={"content": "x"})

        assert response.status_code == 401

    def test_returns_404_when_process_missing(self, client, user_headers):
        response = client.post(
            _url(999999), json={"content": "x"}, headers=user_headers
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROCESS_NOT_FOUND"

    def test_returns_422_empty_content(self, client, user_headers, process_fixture):
        response = client.post(
            _url(process_fixture.id), json={"content": ""}, headers=user_headers
        )

        assert response.status_code == 422

    def test_returns_422_content_too_long(
        self, client, user_headers, process_fixture
    ):
        response = client.post(
            _url(process_fixture.id),
            json={"content": "a" * 5001},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_creates_note(
        self, client, user_headers, active_user, process_fixture, created_note_ids
    ):
        response = client.post(
            _url(process_fixture.id),
            json={"content": "estratégia: aguardar prazo"},
            headers=user_headers,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["process_id"] == process_fixture.id
        assert data["content"] == "estratégia: aguardar prazo"
        assert data["created_by"] == active_user["id"]
        assert data["created_by_name"] == "Active User"
        assert data["updated_by"] is None
        assert data["updated_by_name"] is None
        created_note_ids.append(data["id"])


class TestListNotes:
    def test_returns_401_without_token(self, client, process_fixture):
        response = client.get(_url(process_fixture.id))

        assert response.status_code == 401

    def test_returns_404_when_process_missing(self, client, user_headers):
        response = client.get(_url(999999), headers=user_headers)

        assert response.status_code == 404

    def test_lists_ordered_desc(
        self,
        client,
        user_headers,
        active_user,
        process_fixture,
        db_session,
        created_note_ids,
    ):
        repo = ProcessRepository(db_session)
        first = repo.create_note(
            process_id=process_fixture.id,
            created_by=active_user["id"],
            content="primeira",
        )
        second = repo.create_note(
            process_id=process_fixture.id,
            created_by=active_user["id"],
            content="segunda",
        )
        created_note_ids.extend([first.id, second.id])

        response = client.get(_url(process_fixture.id), headers=user_headers)

        assert response.status_code == 200
        body = response.json()
        ids = [n["id"] for n in body["data"]]
        assert ids.index(second.id) < ids.index(first.id)
        assert body["meta"]["total"] >= 2


class TestUpdateNote:
    def test_returns_401_without_token(self, client, process_fixture):
        response = client.patch(
            f"{_url(process_fixture.id)}/1", json={"content": "x"}
        )

        assert response.status_code == 401

    def test_returns_404_when_note_missing(
        self, client, user_headers, process_fixture
    ):
        response = client.patch(
            f"{_url(process_fixture.id)}/999999",
            json={"content": "x"},
            headers=user_headers,
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROCESS_NOTE_NOT_FOUND"

    def test_returns_404_when_note_from_other_process(
        self,
        client,
        user_headers,
        active_user,
        process_fixture,
        db_session,
        created_note_ids,
        created_process_ids,
        created_client_ids,
    ):
        other_client = ClientRepository(db_session).create(
            name="Outro NotesE2E", cpf="77788899900"
        )
        created_client_ids.append(other_client.id)
        other_process = ProcessRepository(db_session).create(
            number="12345678920248265501",
            client_id=other_client.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        created_process_ids.append(other_process.id)
        note_in_other = ProcessRepository(db_session).create_note(
            process_id=other_process.id,
            created_by=active_user["id"],
            content="alheia",
        )
        created_note_ids.append(note_in_other.id)

        response = client.patch(
            f"{_url(process_fixture.id)}/{note_in_other.id}",
            json={"content": "novo"},
            headers=user_headers,
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROCESS_NOTE_NOT_FOUND"

    def test_author_can_update(
        self,
        client,
        user_headers,
        active_user,
        process_fixture,
        db_session,
        created_note_ids,
    ):
        note = ProcessRepository(db_session).create_note(
            process_id=process_fixture.id,
            created_by=active_user["id"],
            content="antiga",
        )
        created_note_ids.append(note.id)

        response = client.patch(
            f"{_url(process_fixture.id)}/{note.id}",
            json={"content": "atualizada"},
            headers=user_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["content"] == "atualizada"
        assert data["updated_by"] == active_user["id"]
        assert data["updated_by_name"] == "Active User"

    def test_other_user_forbidden(
        self,
        client,
        user_headers,
        admin_user,
        process_fixture,
        db_session,
        created_note_ids,
    ):
        note = ProcessRepository(db_session).create_note(
            process_id=process_fixture.id,
            created_by=admin_user["id"],
            content="do admin",
        )
        created_note_ids.append(note.id)

        response = client.patch(
            f"{_url(process_fixture.id)}/{note.id}",
            json={"content": "tentando"},
            headers=user_headers,
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"

    def test_admin_can_update_any_note(
        self,
        client,
        admin_headers,
        active_user,
        process_fixture,
        db_session,
        created_note_ids,
    ):
        note = ProcessRepository(db_session).create_note(
            process_id=process_fixture.id,
            created_by=active_user["id"],
            content="do user",
        )
        created_note_ids.append(note.id)

        response = client.patch(
            f"{_url(process_fixture.id)}/{note.id}",
            json={"content": "editado por admin"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["content"] == "editado por admin"

    def test_returns_422_content_too_long(
        self,
        client,
        user_headers,
        active_user,
        process_fixture,
        db_session,
        created_note_ids,
    ):
        note = ProcessRepository(db_session).create_note(
            process_id=process_fixture.id,
            created_by=active_user["id"],
            content="ok",
        )
        created_note_ids.append(note.id)

        response = client.patch(
            f"{_url(process_fixture.id)}/{note.id}",
            json={"content": "a" * 5001},
            headers=user_headers,
        )

        assert response.status_code == 422


class TestSeparationFromMovements:
    def test_note_does_not_appear_in_movements(
        self,
        client,
        user_headers,
        process_fixture,
        created_note_ids,
    ):
        marker = "ANOTACAO_INTERNA_NAO_PUBLICA_XYZ"

        create_response = client.post(
            _url(process_fixture.id),
            json={"content": marker},
            headers=user_headers,
        )
        assert create_response.status_code == 201
        created_note_ids.append(create_response.json()["data"]["id"])

        movements_response = client.get(
            f"/api/v1/processes/{process_fixture.id}/movements",
            headers=user_headers,
        )
        assert movements_response.status_code == 200
        movements = movements_response.json()["data"]

        for m in movements:
            assert marker not in (m.get("title") or "")
            assert marker not in (m.get("description") or "")
