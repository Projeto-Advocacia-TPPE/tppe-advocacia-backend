from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import (
    MovementSource,
    Process,
    ProcessStatus,
)
from app.modules.processes.repository import ProcessRepository


@pytest.fixture
def client_fixture(db: Session) -> Client:
    return ClientRepository(db).create(name="Cliente Teste", cpf="11122233344")


@pytest.fixture
def other_client(db: Session) -> Client:
    return ClientRepository(db).create(name="Outro Cliente", cpf="55566677788")


def make_process(
    repo: ProcessRepository, client: Client, number: str, **kwargs
) -> Process:
    defaults = {
        "number": number,
        "client_id": client.id,
        "court": "TJSP",
        "action_type": "Ação Cível",
        "created_by": None,
    }
    defaults.update(kwargs)
    return repo.create(**defaults)


class TestCreate:
    def test_persists_process_with_defaults(self, db: Session, client_fixture):
        repo = ProcessRepository(db)

        process = make_process(repo, client_fixture, "12345678920248260100")

        assert process.id is not None
        assert process.number == "12345678920248260100"
        assert process.status == ProcessStatus.ATIVO
        assert process.client_id == client_fixture.id
        assert process.created_at is not None

    def test_persists_created_by(self, db: Session, client_fixture):
        repo = ProcessRepository(db)

        process = make_process(
            repo, client_fixture, "12345678920248260101", created_by=42
        )

        assert process.created_by == 42
        assert process.updated_by == 42

    def test_number_unique_constraint(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        make_process(repo, client_fixture, "12345678920248260200")

        with pytest.raises(IntegrityError):
            make_process(repo, client_fixture, "12345678920248260200")


class TestGetters:
    def test_get_by_id_returns_with_client(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        created = make_process(repo, client_fixture, "12345678920248260300")

        found = repo.get_by_id(created.id)

        assert found is not None
        assert found.client.name == client_fixture.name

    def test_get_by_id_none_when_missing(self, db: Session):
        assert ProcessRepository(db).get_by_id(99999) is None

    def test_get_by_number_returns_process(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        created = make_process(repo, client_fixture, "12345678920248260400")

        found = repo.get_by_number("12345678920248260400")

        assert found is not None
        assert found.id == created.id


class TestList:
    def test_filter_by_client(self, db: Session, client_fixture, other_client):
        repo = ProcessRepository(db)
        make_process(repo, client_fixture, "12345678920248260501")
        make_process(repo, other_client, "12345678920248260502")

        items, total = repo.list(client_id=client_fixture.id)

        assert total == 1
        assert items[0].client_id == client_fixture.id

    def test_filter_by_status(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        p = make_process(repo, client_fixture, "12345678920248260601")
        p.status = ProcessStatus.SUSPENSO
        db.commit()
        make_process(repo, client_fixture, "12345678920248260602")

        items, total = repo.list(status=ProcessStatus.SUSPENSO)

        assert total == 1
        assert items[0].status == ProcessStatus.SUSPENSO

    def test_search_by_number(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        make_process(repo, client_fixture, "98765432120248260700")

        items, total = repo.list(search="9876543")

        assert total == 1
        assert items[0].number.startswith("9876543")

    def test_search_by_action_type(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        make_process(
            repo,
            client_fixture,
            "12345678920248260800",
            action_type="Ação Trabalhista",
        )

        items, total = repo.list(search="trabalhista")

        assert total == 1
        assert items[0].action_type == "Ação Trabalhista"

    def test_pagination_limits(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        for i in range(3):
            make_process(repo, client_fixture, f"1234567892024826090{i}")

        items, total = repo.list(client_id=client_fixture.id, page=1, limit=2)

        assert len(items) <= 2
        assert total >= 3

    def test_list_by_client(self, db: Session, client_fixture, other_client):
        repo = ProcessRepository(db)
        make_process(repo, client_fixture, "12345678920248261001")
        make_process(repo, other_client, "12345678920248261002")

        items, total = repo.list_by_client(client_fixture.id)

        assert total == 1
        assert items[0].client_id == client_fixture.id


class TestAtomicStatusChange:
    def test_status_update_and_movement_persist_together(
        self, db: Session, client_fixture
    ):
        repo = ProcessRepository(db)
        process = make_process(repo, client_fixture, "12345678920248262300")

        repo.update_status_no_commit(process, ProcessStatus.SUSPENSO, updated_by=42)
        movement = repo.create_movement_no_commit(
            process_id=process.id,
            title="Status alterado: ATIVO -> SUSPENSO",
            description="motivo",
            occurred_at=datetime.now(timezone.utc),
            source=MovementSource.SYSTEM,
            created_by=42,
        )
        db.commit()

        reloaded = repo.get_by_id(process.id)
        assert reloaded.status == ProcessStatus.SUSPENSO
        assert reloaded.updated_by == 42

        movements, total = repo.list_movements(process.id, source=MovementSource.SYSTEM)
        assert total == 1
        assert movements[0].id == movement.id
        assert movements[0].title == "Status alterado: ATIVO -> SUSPENSO"
        assert movements[0].description == "motivo"

    def test_rollback_leaves_status_and_movement_unchanged(
        self, db: Session, client_fixture
    ):
        repo = ProcessRepository(db)
        process = make_process(repo, client_fixture, "12345678920248262301")
        db.commit()

        repo.update_status_no_commit(process, ProcessStatus.SUSPENSO, updated_by=42)
        repo.create_movement_no_commit(
            process_id=process.id,
            title="should be discarded",
            occurred_at=datetime.now(timezone.utc),
            source=MovementSource.SYSTEM,
        )
        db.rollback()

        reloaded = repo.get_by_id(process.id)
        assert reloaded.status == ProcessStatus.ATIVO

        movements, total = repo.list_movements(process.id)
        assert total == 0


class TestCreateProcessAlsoCreatesSystemMovement:
    def test_create_via_service_persists_initial_movement(
        self, db: Session, client_fixture
    ):
        from unittest.mock import MagicMock

        from app.modules.clients.repository import ClientRepository as CR
        from app.modules.processes.schema import ProcessCreate
        from app.modules.processes.service import ProcessService
        from app.modules.users.model import User

        repo = ProcessRepository(db)
        svc = ProcessService(repo, CR(db))

        actor = MagicMock(spec=User)
        actor.id = 7

        payload = ProcessCreate(
            number="1234567-89.2024.8.26.2400",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        process = svc.create_process(payload, created_by=actor)

        movements, total = repo.list_movements(process.id)
        assert total == 1
        assert movements[0].title == "Processo cadastrado"
        assert movements[0].source == MovementSource.SYSTEM
        assert movements[0].created_by == 7
