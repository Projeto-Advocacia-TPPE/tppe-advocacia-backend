from datetime import datetime, timezone

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.main import app
from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.datajud.deps import get_datajud_client
from app.modules.datajud.fake_service import FakeDataJudService
from app.modules.datajud.schema import DataJudMovement
from app.modules.external_api_logs.model import ExternalApiLog
from app.modules.processes.model import Process
from app.modules.processes.repository import ProcessRepository


@pytest.fixture
def datajud_fake():
    service = FakeDataJudService(
        movements=[
            DataJudMovement(
                external_id="e2e-mov-1",
                title="Conclusos para decisão",
                description="Importado do DataJud",
                occurred_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )
        ]
    )
    app.dependency_overrides[get_datajud_client] = lambda: service
    yield service
    app.dependency_overrides.pop(get_datajud_client, None)


@pytest.fixture
def created_records(db_session: Session):
    records = {"process_ids": [], "client_ids": []}
    yield records
    db_session.execute(
        delete(ExternalApiLog).where(
            ExternalApiLog.process_id.in_(records["process_ids"])
        )
    )
    db_session.execute(delete(Process).where(Process.id.in_(records["process_ids"])))
    db_session.execute(delete(Client).where(Client.id.in_(records["client_ids"])))
    db_session.commit()


@pytest.fixture
def client_fixture(db_session: Session, created_records):
    client = ClientRepository(db_session).create(
        name="Cliente E2E DataJud",
        cpf="12312312312",
    )
    db_session.commit()
    created_records["client_ids"].append(client.id)
    return client


class TestDataJudSyncEndpoint:
    def test_sync_process_imports_movements(
        self,
        client,
        user_headers,
        client_fixture,
        created_records,
        datajud_fake,
    ):
        create_response = client.post(
            "/api/v1/processes",
            json={
                "number": "1234567-89.2024.8.26.9100",
                "client_id": client_fixture.id,
                "court": "TJSP",
                "tribunal_alias": "tjsp",
                "action_type": "Ação Cível",
            },
            headers=user_headers,
        )
        assert create_response.status_code == 201
        process_id = create_response.json()["data"]["id"]
        created_records["process_ids"].append(process_id)

        response = client.post(
            f"/api/v1/processes/{process_id}/sync",
            json={},
            headers=user_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["imported_count"] == 1
        assert data["skipped_count"] == 0
        assert data["tribunal_alias"] == "tjsp"
        assert datajud_fake.calls == [("12345678920248269100", "tjsp")]
        assert data["movements"][0]["source"] == "SYSTEM"
        assert data["movements"][0]["external_id"] == "e2e-mov-1"

        list_response = client.get(
            f"/api/v1/processes/{process_id}/movements",
            headers=user_headers,
        )
        assert list_response.status_code == 200
        movements = list_response.json()["data"]
        assert any(m["external_id"] == "e2e-mov-1" for m in movements)

    def test_sync_requires_tribunal_alias(
        self,
        client,
        user_headers,
        client_fixture,
        created_records,
        db_session: Session,
        datajud_fake,
    ):
        process = ProcessRepository(db_session).create(
            number="12345678920248269101",
            client_id=client_fixture.id,
            court="TJSP",
            action_type="Ação Cível",
        )
        db_session.commit()
        created_records["process_ids"].append(process.id)

        response = client.post(
            f"/api/v1/processes/{process.id}/sync",
            json={},
            headers=user_headers,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "DATAJUD_TRIBUNAL_ALIAS_REQUIRED"
