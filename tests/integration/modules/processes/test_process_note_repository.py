import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import Process, ProcessNote
from app.modules.processes.repository import ProcessRepository
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.shared.types import Role


@pytest.fixture
def author(db: Session) -> User:
    return UserRepository(db).create(
        name="Autor",
        email="autor@test.com",
        hashed_password="x",
        role=Role.USER,
    )


@pytest.fixture
def process_fixture(db: Session) -> Process:
    client = ClientRepository(db).create(name="Cliente Note", cpf="11122244400")
    return ProcessRepository(db).create(
        number="12345678920248264400",
        client_id=client.id,
        court="TJSP",
        action_type="Ação Cível",
    )


class TestCreateNote:
    def test_persists_with_creator_relationship(
        self, db: Session, process_fixture, author
    ):
        repo = ProcessRepository(db)

        note = repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="anotacao"
        )

        assert note.id is not None
        assert note.content == "anotacao"
        assert note.process_id == process_fixture.id
        assert note.created_by == author.id
        assert note.creator is not None
        assert note.creator.name == "Autor"
        assert note.updated_by is None


class TestGetNoteById:
    def test_returns_when_process_matches(self, db: Session, process_fixture, author):
        repo = ProcessRepository(db)
        created = repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="a"
        )

        found = repo.get_note_by_id(note_id=created.id, process_id=process_fixture.id)

        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_process_id_mismatches(
        self, db: Session, process_fixture, author
    ):
        repo = ProcessRepository(db)
        other_client = ClientRepository(db).create(name="Outro", cpf="22255566688")
        other_process = repo.create(
            number="12345678920248264401",
            client_id=other_client.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        created = repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="a"
        )

        found = repo.get_note_by_id(note_id=created.id, process_id=other_process.id)

        assert found is None


class TestListNotes:
    def test_orders_created_at_desc_then_id_desc(
        self, db: Session, process_fixture, author
    ):
        repo = ProcessRepository(db)
        first = repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="primeira"
        )
        second = repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="segunda"
        )
        third = repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="terceira"
        )

        notes, total = repo.list_notes_by_process(process_fixture.id)

        assert total == 3
        assert [n.id for n in notes] == [third.id, second.id, first.id]

    def test_pagination(self, db: Session, process_fixture, author):
        repo = ProcessRepository(db)
        for i in range(3):
            repo.create_note(
                process_id=process_fixture.id, created_by=author.id, content=f"n{i}"
            )

        notes, total = repo.list_notes_by_process(process_fixture.id, page=1, limit=2)

        assert total == 3
        assert len(notes) == 2

    def test_isolates_by_process(self, db: Session, process_fixture, author):
        repo = ProcessRepository(db)
        other_client = ClientRepository(db).create(name="O2", cpf="33344455500")
        other_process = repo.create(
            number="12345678920248264402",
            client_id=other_client.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="aqui"
        )
        repo.create_note(
            process_id=other_process.id, created_by=author.id, content="la"
        )

        notes, total = repo.list_notes_by_process(process_fixture.id)

        assert total == 1
        assert notes[0].content == "aqui"


class TestUpdateNote:
    def test_updates_content_and_updater(self, db: Session, process_fixture, author):
        repo = ProcessRepository(db)
        other_user = UserRepository(db).create(
            name="Outro",
            email="outro@test.com",
            hashed_password="x",
            role=Role.ADMIN,
        )
        note = repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="antiga"
        )

        updated = repo.update_note(note, content="nova", updated_by=other_user.id)

        assert updated.content == "nova"
        assert updated.updated_by == other_user.id
        assert updated.updater is not None
        assert updated.updater.name == "Outro"


class TestCascadeDelete:
    def test_notes_deleted_when_process_deleted(
        self, db: Session, process_fixture, author
    ):
        db.execute(text("PRAGMA foreign_keys=ON"))
        repo = ProcessRepository(db)
        repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="a"
        )
        repo.create_note(
            process_id=process_fixture.id, created_by=author.id, content="b"
        )

        db.delete(process_fixture)
        db.commit()

        remaining = db.scalars(
            select(ProcessNote).where(ProcessNote.process_id == process_fixture.id)
        ).all()
        assert remaining == []
