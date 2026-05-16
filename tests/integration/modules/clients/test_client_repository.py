import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository


def make_client(repo: ClientRepository, **kwargs) -> Client:
    defaults = {
        "name": "João Silva",
        "cpf": "12345678901",
    }
    defaults.update(kwargs)
    return repo.create(**defaults)


class TestCreate:
    def test_persists_client_with_cpf(self, db: Session):
        repo = ClientRepository(db)

        client = make_client(repo, name="Maria Souza", cpf="98765432100")

        assert client.id is not None
        assert client.name == "Maria Souza"
        assert client.cpf == "98765432100"
        assert client.cnpj is None
        assert client.created_at is not None
        assert client.created_by is None
        assert client.updated_by is None

    def test_persists_created_by(self, db: Session):
        repo = ClientRepository(db)

        client = make_client(repo, cpf="10203040506", created_by=99)

        assert client.created_by == 99
        assert client.updated_by == 99

    def test_persists_client_with_cnpj(self, db: Session):
        repo = ClientRepository(db)

        client = make_client(repo, name="Empresa X", cpf=None, cnpj="12345678000195")

        assert client.id is not None
        assert client.cnpj == "12345678000195"
        assert client.cpf is None

    def test_cpf_unique_constraint(self, db: Session):
        repo = ClientRepository(db)
        make_client(repo, cpf="11111111111")

        with pytest.raises(IntegrityError):
            make_client(repo, name="Outro", cpf="11111111111")

    def test_cnpj_unique_constraint(self, db: Session):
        repo = ClientRepository(db)
        make_client(repo, cpf=None, cnpj="11111111000111")

        with pytest.raises(IntegrityError):
            make_client(repo, name="Outro", cpf=None, cnpj="11111111000111")


class TestGetById:
    def test_returns_client_when_exists(self, db: Session):
        repo = ClientRepository(db)
        created = make_client(repo, cpf="22222222222")

        found = repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_not_exists(self, db: Session):
        repo = ClientRepository(db)

        assert repo.get_by_id(99999) is None


class TestGetByCpfCnpj:
    def test_get_by_cpf_returns_client(self, db: Session):
        repo = ClientRepository(db)
        created = make_client(repo, cpf="33333333333")

        found = repo.get_by_cpf("33333333333")

        assert found is not None
        assert found.id == created.id

    def test_get_by_cpf_returns_none_when_not_exists(self, db: Session):
        repo = ClientRepository(db)

        assert repo.get_by_cpf("00000000000") is None

    def test_get_by_cnpj_returns_client(self, db: Session):
        repo = ClientRepository(db)
        created = make_client(repo, cpf=None, cnpj="22222222000122")

        found = repo.get_by_cnpj("22222222000122")

        assert found is not None
        assert found.id == created.id

    def test_get_by_cnpj_returns_none_when_not_exists(self, db: Session):
        repo = ClientRepository(db)

        assert repo.get_by_cnpj("00000000000000") is None


class TestList:
    def test_returns_all_clients_paginated(self, db: Session):
        repo = ClientRepository(db)
        make_client(repo, cpf="44444444444")
        make_client(repo, cpf="55555555555")

        clients, total = repo.list(page=1, limit=10)

        assert total >= 2
        assert len(clients) >= 2

    def test_search_by_name_partial_case_insensitive(self, db: Session):
        repo = ClientRepository(db)
        make_client(repo, name="Carlos Teste", cpf="66666666666")

        clients, total = repo.list(search="carlos")

        assert total >= 1
        assert any(c.name == "Carlos Teste" for c in clients)

    def test_search_by_cpf_exact(self, db: Session):
        repo = ClientRepository(db)
        make_client(repo, cpf="77777777777")

        clients, total = repo.list(search="77777777777")

        assert total >= 1
        assert any(c.cpf == "77777777777" for c in clients)

    def test_search_by_cnpj_exact(self, db: Session):
        repo = ClientRepository(db)
        make_client(repo, cpf=None, cnpj="33333333000133")

        clients, total = repo.list(search="33333333000133")

        assert total >= 1
        assert any(c.cnpj == "33333333000133" for c in clients)

    def test_pagination_limits_results(self, db: Session):
        repo = ClientRepository(db)
        make_client(repo, cpf="88888888881")
        make_client(repo, cpf="88888888882")
        make_client(repo, cpf="88888888883")

        clients, total = repo.list(page=1, limit=2)

        assert len(clients) <= 2
        assert total >= 3


class TestUpdate:
    def test_updates_name(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="99999999999")

        updated = repo.update(client, {"name": "Nome Atualizado"})

        assert updated.name == "Nome Atualizado"

    def test_updates_address(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="10101010101")

        updated = repo.update(client, {"address": "Rua das Flores, 123"})

        assert updated.address == "Rua das Flores, 123"
