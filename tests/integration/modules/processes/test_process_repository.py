import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import Process, ProcessStatus
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

        process = make_process(repo, client_fixture, "1234567-89.2024.8.26.0100")

        assert process.id is not None
        assert process.number == "1234567-89.2024.8.26.0100"
        assert process.status == ProcessStatus.ATIVO
        assert process.client_id == client_fixture.id
        assert process.created_at is not None

    def test_persists_created_by(self, db: Session, client_fixture):
        repo = ProcessRepository(db)

        process = make_process(
            repo, client_fixture, "1234567-89.2024.8.26.0101", created_by=42
        )

        assert process.created_by == 42
        assert process.updated_by == 42

    def test_number_unique_constraint(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        make_process(repo, client_fixture, "1234567-89.2024.8.26.0200")

        with pytest.raises(IntegrityError):
            make_process(repo, client_fixture, "1234567-89.2024.8.26.0200")


class TestGetters:
    def test_get_by_id_returns_with_client(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        created = make_process(repo, client_fixture, "1234567-89.2024.8.26.0300")

        found = repo.get_by_id(created.id)

        assert found is not None
        assert found.client.name == client_fixture.name

    def test_get_by_id_none_when_missing(self, db: Session):
        assert ProcessRepository(db).get_by_id(99999) is None

    def test_get_by_number_returns_process(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        created = make_process(repo, client_fixture, "1234567-89.2024.8.26.0400")

        found = repo.get_by_number("1234567-89.2024.8.26.0400")

        assert found is not None
        assert found.id == created.id


class TestList:
    def test_filter_by_client(self, db: Session, client_fixture, other_client):
        repo = ProcessRepository(db)
        make_process(repo, client_fixture, "1234567-89.2024.8.26.0501")
        make_process(repo, other_client, "1234567-89.2024.8.26.0502")

        items, total = repo.list(client_id=client_fixture.id)

        assert total == 1
        assert items[0].client_id == client_fixture.id

    def test_filter_by_status(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        p = make_process(repo, client_fixture, "1234567-89.2024.8.26.0601")
        p.status = ProcessStatus.SUSPENSO
        db.commit()
        make_process(repo, client_fixture, "1234567-89.2024.8.26.0602")

        items, total = repo.list(status=ProcessStatus.SUSPENSO)

        assert total == 1
        assert items[0].status == ProcessStatus.SUSPENSO

    def test_search_by_number(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        make_process(repo, client_fixture, "9876543-21.2024.8.26.0700")

        items, total = repo.list(search="9876543")

        assert total == 1
        assert items[0].number.startswith("9876543")

    def test_search_by_action_type(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        make_process(
            repo,
            client_fixture,
            "1234567-89.2024.8.26.0800",
            action_type="Ação Trabalhista",
        )

        items, total = repo.list(search="trabalhista")

        assert total == 1
        assert items[0].action_type == "Ação Trabalhista"

    def test_pagination_limits(self, db: Session, client_fixture):
        repo = ProcessRepository(db)
        for i in range(3):
            make_process(repo, client_fixture, f"1234567-89.2024.8.26.090{i}")

        items, total = repo.list(client_id=client_fixture.id, page=1, limit=2)

        assert len(items) <= 2
        assert total >= 3

    def test_list_by_client(self, db: Session, client_fixture, other_client):
        repo = ProcessRepository(db)
        make_process(repo, client_fixture, "1234567-89.2024.8.26.1001")
        make_process(repo, other_client, "1234567-89.2024.8.26.1002")

        items, total = repo.list_by_client(client_fixture.id)

        assert total == 1
        assert items[0].client_id == client_fixture.id
