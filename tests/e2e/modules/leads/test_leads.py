import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.leads.model import Lead, LeadStatus
from app.modules.leads.repository import LeadRepository

LEADS_URL = "/api/v1/leads"


@pytest.fixture
def created_lead_ids(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(Lead).where(Lead.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def lead(db_session: Session, created_lead_ids):
    repo = LeadRepository(db_session)
    lead = repo.create(
        name="Carlos Teste",
        email="e2e_lead@example.com",
        message="Quero uma consulta",
    )
    created_lead_ids.append(lead.id)
    return lead


class TestListLeads:
    def test_returns_401_without_token(self, client):
        response = client.get(LEADS_URL)

        assert response.status_code == 401

    def test_returns_403_with_user_token(self, client, user_headers):
        response = client.get(LEADS_URL, headers=user_headers)

        assert response.status_code == 403

    def test_returns_200_with_admin_token(self, client, admin_headers):
        response = client.get(LEADS_URL, headers=admin_headers)

        assert response.status_code == 200

    def test_returns_paginated_structure(self, client, admin_headers):
        response = client.get(LEADS_URL, headers=admin_headers)
        body = response.json()

        assert body["success"] is True
        assert "data" in body
        assert "meta" in body
        assert "total" in body["meta"]

    def test_filters_by_status(self, client, admin_headers, lead, db_session):
        LeadRepository(db_session).update(lead, {"status": LeadStatus.FECHADO})

        response = client.get(f"{LEADS_URL}?status=fechado", headers=admin_headers)

        assert response.status_code == 200
        assert all(lead["status"] == "fechado" for lead in response.json()["data"])

    def test_pagination_respects_limit(self, client, admin_headers):
        response = client.get(f"{LEADS_URL}?limit=1", headers=admin_headers)

        assert len(response.json()["data"]) <= 1

    def test_invalid_limit_returns_422(self, client, admin_headers):
        response = client.get(f"{LEADS_URL}?limit=0", headers=admin_headers)

        assert response.status_code == 422


class TestCreateLead:
    def test_returns_201(self, client, created_lead_ids):
        response = client.post(
            LEADS_URL,
            json={"name": "Ana Lima", "email": "e2e_create_lead@example.com"},
        )

        assert response.status_code == 201
        if response.status_code == 201:
            created_lead_ids.append(response.json()["data"]["id"])

    def test_no_auth_required(self, client, created_lead_ids):
        response = client.post(
            LEADS_URL,
            json={"name": "Sem Auth", "email": "e2e_noauth_lead@example.com"},
        )

        assert response.status_code == 201
        created_lead_ids.append(response.json()["data"]["id"])

    def test_lead_has_status_novo(self, client, created_lead_ids):
        response = client.post(
            LEADS_URL,
            json={"name": "Status Novo", "email": "e2e_status_novo@example.com"},
        )

        assert response.json()["data"]["status"] == "novo"
        created_lead_ids.append(response.json()["data"]["id"])

    def test_returns_409_on_duplicate_email_within_window(
        self, client, created_lead_ids
    ):
        email = "e2e_dedup@example.com"
        first = client.post(LEADS_URL, json={"name": "Primeiro", "email": email})
        assert first.status_code == 201
        created_lead_ids.append(first.json()["data"]["id"])

        second = client.post(LEADS_URL, json={"name": "Segundo", "email": email})

        assert second.status_code == 409
        assert second.json()["error"]["code"] == "LEAD_DUPLICATE"

    def test_returns_422_for_invalid_email(self, client):
        response = client.post(
            LEADS_URL,
            json={"name": "Inválido", "email": "nao-e-email"},
        )

        assert response.status_code == 422

    def test_returns_422_when_name_too_short(self, client):
        response = client.post(
            LEADS_URL,
            json={"name": "A", "email": "short@example.com"},
        )

        assert response.status_code == 422


class TestUpdateLead:
    def test_returns_401_without_token(self, client, lead):
        response = client.patch(f"{LEADS_URL}/{lead.id}", json={"status": "FECHADO"})

        assert response.status_code == 401

    def test_returns_403_with_user_token(self, client, lead, user_headers):
        response = client.patch(
            f"{LEADS_URL}/{lead.id}",
            json={"status": "FECHADO"},
            headers=user_headers,
        )

        assert response.status_code == 403

    def test_updates_status(self, client, lead, admin_headers):
        response = client.patch(
            f"{LEADS_URL}/{lead.id}",
            json={"status": "em_atendimento"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "em_atendimento"

    def test_assigns_responsible(self, client, lead, admin_headers, admin_user):
        response = client.patch(
            f"{LEADS_URL}/{lead.id}",
            json={"assigned_to": admin_user["id"]},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["assigned_to"] == admin_user["id"]

    def test_returns_422_when_assignee_not_found(self, client, lead, admin_headers):
        response = client.patch(
            f"{LEADS_URL}/{lead.id}",
            json={"assigned_to": 99999},
            headers=admin_headers,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "ASSIGNEE_NOT_FOUND"

    def test_returns_404_when_lead_not_found(self, client, admin_headers):
        response = client.patch(
            f"{LEADS_URL}/99999",
            json={"status": "fechado"},
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "LEAD_NOT_FOUND"
