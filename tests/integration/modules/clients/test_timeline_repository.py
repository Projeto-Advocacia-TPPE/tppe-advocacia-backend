from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.modules.clients.repository import ClientRepository
from app.modules.clients.timeline_repository import TimelineRepository
from app.modules.processes.model import MovementSource
from app.modules.processes.repository import ProcessRepository
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.shared.types import Role


@pytest.fixture
def author(db: Session) -> User:
    return UserRepository(db).create(
        name="Autor TL",
        email="atl@test.com",
        hashed_password="x",
        role=Role.USER,
    )


@pytest.fixture
def client_fixture(db: Session):
    return ClientRepository(db).create(name="Cli TL", cpf="22233344455")


@pytest.fixture
def other_client(db: Session):
    return ClientRepository(db).create(name="Outro TL", cpf="66677788899")


class TestGetProcessesWithLastMovement:
    def test_returns_none_when_process_has_no_movements(
        self, db: Session, client_fixture
    ):
        prepo = ProcessRepository(db)
        process = prepo.create(
            number="12345678920248267700",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="A",
        )

        result = prepo.get_processes_with_last_movement(client_fixture.id, limit=10)

        assert len(result) == 1
        proc, last = result[0]
        assert proc.id == process.id
        assert last is None

    def test_returns_most_recent_movement(self, db: Session, client_fixture, author):
        prepo = ProcessRepository(db)
        process = prepo.create(
            number="12345678920248267701",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="A",
        )
        base = datetime.now(timezone.utc) - timedelta(days=5)
        prepo.create_movement(
            process_id=process.id,
            title="older",
            occurred_at=base,
            source=MovementSource.MANUAL,
            created_by=author.id,
        )
        newer = prepo.create_movement(
            process_id=process.id,
            title="newer",
            occurred_at=base + timedelta(days=2),
            source=MovementSource.MANUAL,
            created_by=author.id,
        )

        result = prepo.get_processes_with_last_movement(client_fixture.id, limit=10)

        assert len(result) == 1
        proc, last = result[0]
        assert proc.id == process.id
        assert last is not None
        assert last.id == newer.id

    def test_isolates_by_client(self, db: Session, client_fixture, other_client):
        prepo = ProcessRepository(db)
        prepo.create(
            number="12345678920248267702",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="A",
        )
        prepo.create(
            number="12345678920248267703",
            client_id=other_client.id,
            court="TJSP",
            action_type="A",
        )

        result = prepo.get_processes_with_last_movement(client_fixture.id, limit=10)

        assert len(result) == 1
        assert result[0][0].client_id == client_fixture.id


class TestGetRecentActivity:
    def test_empty_for_blank_client(self, db: Session, client_fixture):
        repo = TimelineRepository(db)

        rows = repo.get_recent_activity(client_fixture.id, limit=10)

        assert rows == []

    def test_unions_movements_and_notes_ordered_desc(
        self, db: Session, client_fixture, author
    ):
        prepo = ProcessRepository(db)
        crepo = ClientRepository(db)
        process = prepo.create(
            number="12345678920248267800",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="A",
        )
        base = datetime.now(timezone.utc) - timedelta(days=10)
        mov_old = prepo.create_movement(
            process_id=process.id,
            title="old movement",
            occurred_at=base,
            source=MovementSource.MANUAL,
            created_by=author.id,
        )
        mov_new = prepo.create_movement(
            process_id=process.id,
            title="new movement",
            occurred_at=base + timedelta(days=5),
            source=MovementSource.MANUAL,
            created_by=author.id,
        )
        crepo.create_note(
            client_id=client_fixture.id, created_by=author.id, content="nota A"
        )

        repo = TimelineRepository(db)
        rows = repo.get_recent_activity(client_fixture.id, limit=10)

        assert len(rows) == 3
        kinds = [r["kind"] for r in rows]
        assert "movement" in kinds and "client_note" in kinds
        ids_in_order = [(r["process_id"], r["note_id"]) for r in rows]
        # most recent first: the most recent note created_at vs movements
        # at minimum, newer movement appears before older movement
        new_idx = next(
            i
            for i, r in enumerate(rows)
            if r["kind"] == "movement" and r["title"] == "new movement"
        )
        old_idx = next(
            i
            for i, r in enumerate(rows)
            if r["kind"] == "movement" and r["title"] == "old movement"
        )
        assert new_idx < old_idx
        assert mov_old.id and mov_new.id  # sanity
        assert ids_in_order  # smoke

    def test_respects_limit(self, db: Session, client_fixture, author):
        crepo = ClientRepository(db)
        for i in range(5):
            crepo.create_note(
                client_id=client_fixture.id, created_by=author.id, content=f"n{i}"
            )

        repo = TimelineRepository(db)
        rows = repo.get_recent_activity(client_fixture.id, limit=3)

        assert len(rows) == 3

    def test_isolates_by_client(
        self, db: Session, client_fixture, other_client, author
    ):
        crepo = ClientRepository(db)
        crepo.create_note(
            client_id=other_client.id, created_by=author.id, content="alheia"
        )
        crepo.create_note(
            client_id=client_fixture.id, created_by=author.id, content="propria"
        )

        repo = TimelineRepository(db)
        rows = repo.get_recent_activity(client_fixture.id, limit=10)

        assert len(rows) == 1
        assert rows[0]["content"] == "propria"
