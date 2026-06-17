import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository

CLIENTS_URL = "/api/v1/clients"


@pytest.fixture
def created_client_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(Client).where(Client.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def client_cpf(db_session: Session, created_client_ids):
    repo = ClientRepository(db_session)
    c = repo.create(name="Carlos Teste", cpf="12345678901")
    db_session.commit()
    created_client_ids.append(c.id)
    return c


@pytest.fixture
def client_cnpj(db_session: Session, created_client_ids):
    repo = ClientRepository(db_session)
    c = repo.create(name="Empresa Teste", cnpj="12345678000195")
    db_session.commit()
    created_client_ids.append(c.id)
    return c


class TestCreateClient:
    def test_returns_401_without_token(self, client):
        response = client.post(CLIENTS_URL, json={"name": "João", "cpf": "12345678901"})

        assert response.status_code == 401

    def test_creates_with_cpf(
        self, client, user_headers, active_user, created_client_ids
    ):
        response = client.post(
            CLIENTS_URL,
            json={"name": "João Silva", "cpf": "11122233344"},
            headers=user_headers,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["cpf"] == "11122233344"
        assert data["cnpj"] is None
        assert data["created_by"] == active_user["id"]
        assert data["updated_by"] == active_user["id"]
        created_client_ids.append(data["id"])

    def test_creates_with_cnpj(self, client, user_headers, created_client_ids):
        response = client.post(
            CLIENTS_URL,
            json={"name": "Empresa X", "cnpj": "11222333000181"},
            headers=user_headers,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["cnpj"] == "11222333000181"
        created_client_ids.append(data["id"])

    def test_returns_422_without_cpf_or_cnpj(self, client, user_headers):
        response = client.post(
            CLIENTS_URL,
            json={"name": "Sem Documento"},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_returns_422_with_both_cpf_and_cnpj(self, client, user_headers):
        response = client.post(
            CLIENTS_URL,
            json={"name": "Ambos", "cpf": "12345678901", "cnpj": "12345678000195"},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_returns_409_on_duplicate_cpf(
        self, client, user_headers, client_cpf, created_client_ids
    ):
        response = client.post(
            CLIENTS_URL,
            json={"name": "Outro", "cpf": client_cpf.cpf},
            headers=user_headers,
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CLIENT_CPF_ALREADY_EXISTS"

    def test_returns_409_on_duplicate_cnpj(
        self, client, user_headers, client_cnpj, created_client_ids
    ):
        response = client.post(
            CLIENTS_URL,
            json={"name": "Outra Empresa", "cnpj": client_cnpj.cnpj},
            headers=user_headers,
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CLIENT_CNPJ_ALREADY_EXISTS"

    def test_returns_422_for_invalid_cpf_format(self, client, user_headers):
        response = client.post(
            CLIENTS_URL,
            json={"name": "CPF Inválido", "cpf": "123"},
            headers=user_headers,
        )

        assert response.status_code == 422


class TestListClients:
    def test_returns_401_without_token(self, client):
        response = client.get(CLIENTS_URL)

        assert response.status_code == 401

    def test_returns_paginated_structure(self, client, user_headers):
        response = client.get(CLIENTS_URL, headers=user_headers)
        body = response.json()

        assert body["success"] is True
        assert "data" in body
        assert "meta" in body
        assert "total" in body["meta"]

    def test_search_by_name(self, client, user_headers, client_cpf):
        response = client.get(f"{CLIENTS_URL}?search=Carlos", headers=user_headers)

        assert response.status_code == 200
        assert any(c["name"] == "Carlos Teste" for c in response.json()["data"])

    def test_search_by_cpf(self, client, user_headers, client_cpf):
        response = client.get(
            f"{CLIENTS_URL}?search={client_cpf.cpf}", headers=user_headers
        )

        assert response.status_code == 200
        assert any(c["cpf"] == client_cpf.cpf for c in response.json()["data"])

    def test_pagination_respects_limit(self, client, user_headers):
        response = client.get(f"{CLIENTS_URL}?limit=1", headers=user_headers)

        assert len(response.json()["data"]) <= 1

    def test_invalid_limit_returns_422(self, client, user_headers):
        response = client.get(f"{CLIENTS_URL}?limit=0", headers=user_headers)

        assert response.status_code == 422


class TestGetClient:
    def test_returns_401_without_token(self, client, client_cpf):
        response = client.get(f"{CLIENTS_URL}/{client_cpf.id}")

        assert response.status_code == 401

    def test_returns_client_data(self, client, user_headers, client_cpf):
        response = client.get(f"{CLIENTS_URL}/{client_cpf.id}", headers=user_headers)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == client_cpf.id
        assert data["name"] == "Carlos Teste"

    def test_returns_404_when_not_found(self, client, user_headers):
        response = client.get(f"{CLIENTS_URL}/99999", headers=user_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CLIENT_NOT_FOUND"


class TestUpdateClient:
    def test_returns_401_without_token(self, client, client_cpf):
        response = client.patch(f"{CLIENTS_URL}/{client_cpf.id}", json={"name": "Novo"})

        assert response.status_code == 401

    def test_updates_name(self, client, user_headers, active_user, client_cpf):
        response = client.patch(
            f"{CLIENTS_URL}/{client_cpf.id}",
            json={"name": "Nome Atualizado"},
            headers=user_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "Nome Atualizado"
        assert data["updated_by"] == active_user["id"]

    def test_updates_address(self, client, user_headers, client_cpf):
        response = client.patch(
            f"{CLIENTS_URL}/{client_cpf.id}",
            json={"address": "Rua das Flores, 123"},
            headers=user_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["address"] == "Rua das Flores, 123"

    def test_returns_404_when_not_found(self, client, user_headers):
        response = client.patch(
            f"{CLIENTS_URL}/99999",
            json={"name": "Não existe"},
            headers=user_headers,
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CLIENT_NOT_FOUND"

    def test_returns_409_on_duplicate_cpf(
        self, client, user_headers, client_cpf, created_client_ids, db_session
    ):
        repo = ClientRepository(db_session)
        other = repo.create(name="Outro Cliente", cpf="99988877766")
        db_session.commit()
        created_client_ids.append(other.id)

        response = client.patch(
            f"{CLIENTS_URL}/{other.id}",
            json={"cpf": client_cpf.cpf},
            headers=user_headers,
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CLIENT_CPF_ALREADY_EXISTS"

    def test_returns_422_with_both_cpf_and_cnpj(self, client, user_headers, client_cpf):
        response = client.patch(
            f"{CLIENTS_URL}/{client_cpf.id}",
            json={"cpf": "11111111111", "cnpj": "11111111000111"},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_switching_to_cnpj_nullifies_cpf(self, client, user_headers, client_cpf):
        response = client.patch(
            f"{CLIENTS_URL}/{client_cpf.id}",
            json={"cnpj": "99988877000166"},
            headers=user_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["cnpj"] == "99988877000166"
        assert data["cpf"] is None
