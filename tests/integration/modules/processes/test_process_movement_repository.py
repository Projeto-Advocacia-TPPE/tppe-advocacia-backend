from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import MovementSource, Process, ProcessMovement
from app.modules.processes.repository import ProcessRepository


@pytest.fixture
def process_fixture(db: Session) -> Process:
    client = ClientRepository(db).create(name="Cliente MovTest", cpf="11122233355")
    return ProcessRepository(db).create(
        number="12345678920248262100",
        client_id=client.id,
        court="TJSP",
        action_type="Ação Cível",
    )


def make_movement(
    repo: ProcessRepository,
    process: Process,
    title: str = "Movimento",
    occurred_at: datetime | None = None,
    source: MovementSource = MovementSource.MANUAL,
    description: str | None = None,
    created_by: int | None = None,
) -> ProcessMovement:
    return repo.create_movement(
        process_id=process.id,
        title=title,
        description=description,
        occurred_at=occurred_at or datetime.now(timezone.utc),
        source=source,
        created_by=created_by,
    )


class TestCreateMovement:
    def test_persists_with_defaults(self, db: Session, process_fixture):
        repo = ProcessRepository(db)

        movement = make_movement(repo, process_fixture, title="Audiência")

        assert movement.id is not None
        assert movement.title == "Audiência"
        assert movement.source == MovementSource.MANUAL
        assert movement.process_id == process_fixture.id
        assert movement.created_at is not None


class TestListMovements:
    def test_orders_by_occurred_at_desc_then_id_desc(
        self, db: Session, process_fixture
    ):
        repo = ProcessRepository(db)
        base = datetime.now(timezone.utc) - timedelta(days=5)

        older = make_movement(repo, process_fixture, title="A", occurred_at=base)
        same_a = make_movement(
            repo, process_fixture, title="B", occurred_at=base + timedelta(days=1)
        )
        same_b = make_movement(
            repo, process_fixture, title="C", occurred_at=base + timedelta(days=1)
        )
        newest = make_movement(
            repo, process_fixture, title="D", occurred_at=base + timedelta(days=2)
        )

        items, total = repo.list_movements(process_fixture.id)

        assert total == 4
        assert items[0].id == newest.id
        assert items[1].id == same_b.id
        assert items[2].id == same_a.id
        assert items[3].id == older.id

    def test_filter_by_source(self, db: Session, process_fixture):
        repo = ProcessRepository(db)
        make_movement(repo, process_fixture, source=MovementSource.MANUAL)
        make_movement(repo, process_fixture, source=MovementSource.SYSTEM)

        items, total = repo.list_movements(
            process_fixture.id, source=MovementSource.SYSTEM
        )

        assert total == 1
        assert items[0].source == MovementSource.SYSTEM

    def test_filter_by_date_range(self, db: Session, process_fixture):
        repo = ProcessRepository(db)
        old = datetime.now(timezone.utc) - timedelta(days=30)
        recent = datetime.now(timezone.utc) - timedelta(days=2)

        make_movement(repo, process_fixture, title="old", occurred_at=old)
        make_movement(repo, process_fixture, title="recent", occurred_at=recent)

        items, total = repo.list_movements(
            process_fixture.id,
            date_from=datetime.now(timezone.utc) - timedelta(days=7),
        )

        assert total == 1
        assert items[0].title == "recent"

    def test_pagination(self, db: Session, process_fixture):
        repo = ProcessRepository(db)
        for i in range(3):
            make_movement(repo, process_fixture, title=f"m{i}")

        items, total = repo.list_movements(process_fixture.id, page=1, limit=2)

        assert total == 3
        assert len(items) == 2

    def test_isolates_by_process(self, db: Session, process_fixture):
        repo = ProcessRepository(db)
        other_client = ClientRepository(db).create(name="Outro", cpf="99988877766")
        other = repo.create(
            number="12345678920248262101",
            client_id=other_client.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        make_movement(repo, process_fixture, title="A")
        make_movement(repo, other, title="B")

        items, total = repo.list_movements(process_fixture.id)

        assert total == 1
        assert items[0].title == "A"


class TestCascadeDelete:
    def test_movements_deleted_when_process_deleted(self, db: Session, process_fixture):
        db.execute(text("PRAGMA foreign_keys=ON"))
        repo = ProcessRepository(db)
        make_movement(repo, process_fixture, title="X")
        make_movement(repo, process_fixture, title="Y")
        db.commit()

        # SQLite PRAGMA é por conexão; o commit acima pode rotacionar a
        # connection do pool, então reaplicamos antes do DELETE para garantir
        # que o ON DELETE CASCADE seja honrado.
        db.execute(text("PRAGMA foreign_keys=ON"))
        db.delete(process_fixture)
        db.commit()

        remaining = db.scalars(
            select(ProcessMovement).where(
                ProcessMovement.process_id == process_fixture.id
            )
        ).all()
        assert remaining == []
