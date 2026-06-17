from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.modules.clients.model import Client, ClientNote
from app.modules.clients.schema import ClientNoteCreate, ClientNoteUpdate
from app.modules.clients.service import ClientService
from app.modules.users.model import User
from app.shared.exceptions import (
    ClientNoteNotFoundError,
    ClientNotFoundError,
    ForbiddenError,
)
from app.shared.types import Role


def make_client(**kwargs) -> Client:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "name": "João Silva",
        "cpf": "12345678901",
        "cnpj": None,
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


def make_note(**kwargs) -> ClientNote:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "client_id": 1,
        "created_by": 1,
        "updated_by": None,
        "content": "Observação de teste",
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    note = MagicMock(spec=ClientNote)
    for key, value in defaults.items():
        setattr(note, key, value)
    return note


def make_user(user_id: int = 1, role: Role = Role.USER) -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.role = role
    return user


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    svc = ClientService.__new__(ClientService)
    svc.repository = repo
    return svc


class TestCreateNote:
    def test_raises_when_client_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        payload = ClientNoteCreate(content="Nota")

        with pytest.raises(ClientNotFoundError):
            service.create_note(99, payload, current_user=make_user())

        repo.create_note.assert_not_called()

    def test_creates_note_with_current_user_as_author(self, service, repo):
        repo.get_by_id.return_value = make_client()
        note = make_note()
        repo.create_note.return_value = note
        payload = ClientNoteCreate(content="Anotação importante")
        user = make_user(user_id=7)

        result = service.create_note(1, payload, current_user=user)

        assert result is note
        repo.create_note.assert_called_once_with(
            client_id=1, created_by=7, content="Anotação importante"
        )


class TestListNotes:
    def test_raises_when_client_not_found(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ClientNotFoundError):
            service.list_notes(99)

    def test_delegates_to_repository(self, service, repo):
        repo.get_by_id.return_value = make_client()
        repo.list_notes_by_client.return_value = ([], 0)

        notes, total = service.list_notes(1, page=2, limit=5)

        repo.list_notes_by_client.assert_called_once_with(client_id=1, page=2, limit=5)
        assert notes == []
        assert total == 0


class TestUpdateNote:
    def test_raises_when_client_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        payload = ClientNoteUpdate(content="Novo conteúdo")

        with pytest.raises(ClientNotFoundError):
            service.update_note(99, 1, payload, current_user=make_user())

    def test_raises_when_note_not_found(self, service, repo):
        repo.get_by_id.return_value = make_client()
        repo.get_note_by_id.return_value = None
        payload = ClientNoteUpdate(content="Novo conteúdo")

        with pytest.raises(ClientNoteNotFoundError):
            service.update_note(1, 99, payload, current_user=make_user())

    def test_raises_forbidden_when_different_user_not_admin(self, service, repo):
        repo.get_by_id.return_value = make_client()
        note = make_note(created_by=1)
        repo.get_note_by_id.return_value = note
        payload = ClientNoteUpdate(content="Tentativa")
        other_user = make_user(user_id=2, role=Role.USER)

        with pytest.raises(ForbiddenError):
            service.update_note(1, 1, payload, current_user=other_user)

        repo.update_note.assert_not_called()

    def test_author_can_edit_own_note(self, service, repo):
        repo.get_by_id.return_value = make_client()
        note = make_note(created_by=5)
        updated = make_note(created_by=5, content="Editado")
        repo.get_note_by_id.return_value = note
        repo.update_note.return_value = updated
        payload = ClientNoteUpdate(content="Editado")
        author = make_user(user_id=5, role=Role.USER)

        result = service.update_note(1, 1, payload, current_user=author)

        assert result is updated
        repo.update_note.assert_called_once_with(
            note=note, content="Editado", updated_by=5
        )

    def test_admin_can_edit_any_note(self, service, repo):
        repo.get_by_id.return_value = make_client()
        note = make_note(created_by=1)
        updated = make_note(created_by=1, updated_by=99, content="Editado por admin")
        repo.get_note_by_id.return_value = note
        repo.update_note.return_value = updated
        payload = ClientNoteUpdate(content="Editado por admin")
        admin = make_user(user_id=99, role=Role.ADMIN)

        result = service.update_note(1, 1, payload, current_user=admin)

        assert result is updated
        repo.update_note.assert_called_once_with(
            note=note, content="Editado por admin", updated_by=99
        )

    def test_note_from_different_client_raises_not_found(self, service, repo):
        repo.get_by_id.return_value = make_client(id=1)
        repo.get_note_by_id.return_value = None
        payload = ClientNoteUpdate(content="Conteúdo")

        with pytest.raises(ClientNoteNotFoundError):
            service.update_note(1, 1, payload, current_user=make_user())
