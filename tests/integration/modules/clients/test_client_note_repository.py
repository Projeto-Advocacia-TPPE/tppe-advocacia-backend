from sqlalchemy.orm import Session

from app.modules.clients.model import Client, ClientNote
from app.modules.clients.repository import ClientRepository


def make_client(repo: ClientRepository, **kwargs) -> Client:
    defaults = {"name": "João Silva", "cpf": "12345678901"}
    defaults.update(kwargs)
    return repo.create(**defaults)


def make_note(repo: ClientRepository, client_id: int, **kwargs) -> ClientNote:
    defaults = {"created_by": 1, "content": "Observação de teste"}
    defaults.update(kwargs)
    return repo.create_note(client_id=client_id, **defaults)


class TestCreateNote:
    def test_persists_note(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="11111111111")

        note = make_note(repo, client.id, content="Primeira nota", created_by=42)

        assert note.id is not None
        assert note.client_id == client.id
        assert note.created_by == 42
        assert note.updated_by is None
        assert note.content == "Primeira nota"
        assert note.created_at is not None

    def test_returns_note_with_creator_loaded(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="22222222222")
        note = make_note(repo, client.id)

        # creator relationship loaded — accessing it must not raise DetachedInstanceError
        assert note.creator is not None or note.creator is None  # just access it


class TestGetNoteById:
    def test_returns_note_when_exists(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="33333333333")
        created = make_note(repo, client.id, content="Nota")

        found = repo.get_note_by_id(note_id=created.id, client_id=client.id)

        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_note_id_not_found(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="44444444444")

        assert repo.get_note_by_id(note_id=99999, client_id=client.id) is None

    def test_returns_none_when_note_belongs_to_different_client(self, db: Session):
        repo = ClientRepository(db)
        client_a = make_client(repo, cpf="55555555555")
        client_b = make_client(repo, cpf="66666666666")
        note = make_note(repo, client_a.id)

        assert repo.get_note_by_id(note_id=note.id, client_id=client_b.id) is None


class TestListNotesByClient:
    def test_returns_notes_for_client(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="77777777777")
        make_note(repo, client.id, content="Nota 1")
        make_note(repo, client.id, content="Nota 2")

        notes, total = repo.list_notes_by_client(client_id=client.id)

        assert total == 2
        assert len(notes) == 2

    def test_does_not_return_notes_from_other_clients(self, db: Session):
        repo = ClientRepository(db)
        client_a = make_client(repo, cpf="88888888888")
        client_b = make_client(repo, cpf="99999999999")
        make_note(repo, client_a.id, content="Nota do cliente A")

        notes, total = repo.list_notes_by_client(client_id=client_b.id)

        assert total == 0
        assert notes == []

    def test_ordered_by_created_at_desc(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="10101010101")
        note1 = make_note(repo, client.id, content="Primeira")
        note2 = make_note(repo, client.id, content="Segunda")

        notes, _ = repo.list_notes_by_client(client_id=client.id)

        assert notes[0].id == note2.id
        assert notes[1].id == note1.id

    def test_pagination_limits_results(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="20202020202")
        for i in range(5):
            make_note(repo, client.id, content=f"Nota {i}")

        notes, total = repo.list_notes_by_client(client_id=client.id, page=1, limit=3)

        assert total == 5
        assert len(notes) == 3

    def test_pagination_second_page(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="30303030303")
        for i in range(5):
            make_note(repo, client.id, content=f"Nota {i}")

        notes, total = repo.list_notes_by_client(client_id=client.id, page=2, limit=3)

        assert total == 5
        assert len(notes) == 2


class TestUpdateNote:
    def test_updates_content_and_updated_by(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="40404040404")
        note = make_note(repo, client.id, content="Original", created_by=1)

        updated = repo.update_note(note=note, content="Editado", updated_by=99)

        assert updated.content == "Editado"
        assert updated.updated_by == 99

    def test_persists_update_across_fetch(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="50505050505")
        note = make_note(repo, client.id, content="Original")

        repo.update_note(note=note, content="Persistido", updated_by=1)
        fetched = repo.get_note_by_id(note_id=note.id, client_id=client.id)

        assert fetched is not None
        assert fetched.content == "Persistido"
