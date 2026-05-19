from datetime import datetime, timezone

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


class TestAnonymizeAndFiltering:
    def test_anonymize_overwrites_pii_and_sets_deleted_at(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, name="João", cpf="20202020201", address="Rua A")
        note = repo.create_note(client_id=client.id, created_by=1, content="oi")
        now = datetime.now(timezone.utc)

        repo.anonymize_no_commit(client, anonymized_at=now)
        db.commit()
        db.refresh(client)

        assert client.name == "[ANONIMIZADO]"
        assert client.email is None
        assert client.phone is None
        assert client.cpf is None
        assert client.cnpj is None
        assert client.address is None
        assert client.deleted_at is not None

        from sqlalchemy import select

        from app.modules.clients.model import ClientNote

        stored_note = db.scalars(
            select(ClientNote).where(ClientNote.id == note.id)
        ).first()
        assert stored_note.content == "[ANONIMIZADO]"
        assert stored_note.deleted_at is not None

    def test_list_excludes_anonymized(self, db: Session):
        repo = ClientRepository(db)
        active = make_client(repo, name="Ativo", cpf="30303030301")
        deleted = make_client(repo, name="Deletado", cpf="30303030302")
        repo.anonymize_no_commit(deleted, anonymized_at=datetime.now(timezone.utc))
        db.commit()

        clients, total = repo.list(limit=100)
        ids = [c.id for c in clients]

        assert active.id in ids
        assert deleted.id not in ids

    def test_get_by_id_excludes_anonymized_by_default(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="40404040401")
        repo.anonymize_no_commit(client, anonymized_at=datetime.now(timezone.utc))
        db.commit()

        assert repo.get_by_id(client.id) is None
        assert repo.get_by_id(client.id, include_deleted=True) is not None

    def test_get_by_cpf_returns_none_for_anonymized(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="50505050501")
        repo.anonymize_no_commit(client, anonymized_at=datetime.now(timezone.utc))
        db.commit()

        assert repo.get_by_cpf("50505050501") is None

    def test_cpf_can_be_reused_after_anonymize(self, db: Session):
        repo = ClientRepository(db)
        first = make_client(repo, cpf="60606060601")
        repo.anonymize_no_commit(first, anonymized_at=datetime.now(timezone.utc))
        db.commit()

        new_client = make_client(repo, name="Novo Dono", cpf="60606060601")

        assert new_client.id != first.id
        assert new_client.cpf == "60606060601"

    def test_list_notes_excludes_anonymized_notes(self, db: Session):
        repo = ClientRepository(db)
        client = make_client(repo, cpf="70707070701")
        repo.create_note(client_id=client.id, created_by=1, content="visivel")
        repo.anonymize_no_commit(client, anonymized_at=datetime.now(timezone.utc))
        db.commit()

        notes, total = repo.list_notes_by_client(client_id=client.id)

        assert total == 0
        assert notes == []
