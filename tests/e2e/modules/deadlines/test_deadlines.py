import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.deadlines.model import Deadline
from app.modules.forensic_holidays.model import ForensicHoliday
from app.modules.processes.model import Process
from app.modules.processes.repository import ProcessRepository

CALC_URL = "/api/v1/deadlines/calculate"


@pytest.fixture
def cleanup_holidays(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(ForensicHoliday).where(ForensicHoliday.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def cleanup_processes(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(Deadline).where(Deadline.process_id.in_(ids)))
    db_session.execute(delete(Process).where(Process.id.in_(ids)))
    db_session.commit()


@pytest.fixture
def process_fixture(db_session: Session, active_user, cleanup_processes):
    p = ProcessRepository(db_session).create(
        number="99999999999999999991",
        court="TJDFT",
        action_type="Ação Cível",
        created_by=active_user["id"],
    )
    db_session.commit()
    cleanup_processes.append(p.id)
    return p


class TestCalculateEndpoint:
    def test_requires_auth(self, client):
        r = client.post(CALC_URL, json={"start_date": "2026-05-11", "business_days": 5})
        assert r.status_code in (401, 403)

    def test_calculates_simple(self, client, user_headers):
        r = client.post(
            CALC_URL,
            json={"start_date": "2026-05-11", "business_days": 5},
            headers=user_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["due_date"] == "2026-05-18"
        assert isinstance(data["skipped_days"], list)

    def test_rejects_zero_business_days(self, client, user_headers):
        r = client.post(
            CALC_URL,
            json={"start_date": "2026-05-11", "business_days": 0},
            headers=user_headers,
        )
        assert r.status_code == 422


class TestProcessDeadlines:
    def test_create_lists_and_deletes(self, client, user_headers, process_fixture):
        url = f"/api/v1/processes/{process_fixture.id}/deadlines"
        r = client.post(
            url,
            json={
                "start_date": "2026-05-11",
                "business_days": 5,
                "deadline_type": "Contestação",
            },
            headers=user_headers,
        )
        assert r.status_code == 201
        deadline_id = r.json()["data"]["id"]
        assert r.json()["data"]["due_date"] == "2026-05-18"
        assert r.json()["data"]["court"] == "TJDFT"

        list_r = client.get(url, headers=user_headers)
        assert list_r.status_code == 200
        assert any(d["id"] == deadline_id for d in list_r.json()["data"])

        del_r = client.delete(f"/api/v1/deadlines/{deadline_id}", headers=user_headers)
        assert del_r.status_code == 204

    def test_patch_recalculates(self, client, user_headers, process_fixture):
        url = f"/api/v1/processes/{process_fixture.id}/deadlines"
        r = client.post(
            url,
            json={
                "start_date": "2026-05-11",
                "business_days": 5,
                "deadline_type": "Contestação",
            },
            headers=user_headers,
        )
        deadline_id = r.json()["data"]["id"]

        upd = client.patch(
            f"/api/v1/deadlines/{deadline_id}",
            json={"business_days": 10},
            headers=user_headers,
        )
        assert upd.status_code == 200
        # Mon May 11 + 10 biz days = Mon May 25
        assert upd.json()["data"]["due_date"] == "2026-05-25"

    def test_process_not_found(self, client, user_headers):
        r = client.post(
            "/api/v1/processes/99999999/deadlines",
            json={
                "start_date": "2026-05-11",
                "business_days": 5,
                "deadline_type": "x",
            },
            headers=user_headers,
        )
        assert r.status_code == 404
