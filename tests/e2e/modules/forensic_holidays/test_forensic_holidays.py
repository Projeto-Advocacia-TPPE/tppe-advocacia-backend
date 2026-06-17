import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.forensic_holidays.model import ForensicHoliday

URL = "/api/v1/forensic-holidays"


@pytest.fixture
def cleanup_holidays(db_session: Session):
    ids: list[int] = []
    yield ids
    db_session.execute(delete(ForensicHoliday).where(ForensicHoliday.id.in_(ids)))
    db_session.commit()


class TestListHolidays:
    def test_requires_auth(self, client):
        response = client.get(URL)
        assert response.status_code in (401, 403)

    def test_lists_with_user(self, client, user_headers):
        response = client.get(URL, headers=user_headers)
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestCreateHoliday:
    def test_user_forbidden(self, client, user_headers):
        response = client.post(
            URL,
            json={
                "date": "2099-01-01",
                "description": "Teste",
                "scope": "NATIONAL",
            },
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_admin_creates_national(self, client, admin_headers, cleanup_holidays):
        response = client.post(
            URL,
            json={
                "date": "2099-01-01",
                "description": "Teste Nacional",
                "scope": "NATIONAL",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["scope"] == "NATIONAL"
        cleanup_holidays.append(data["id"])

    def test_court_requires_court_field(self, client, admin_headers):
        response = client.post(
            URL,
            json={
                "date": "2099-04-23",
                "description": "x",
                "scope": "COURT",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_admin_creates_court(self, client, admin_headers, cleanup_holidays):
        response = client.post(
            URL,
            json={
                "date": "2099-04-23",
                "description": "Aniv Brasília",
                "scope": "COURT",
                "court": "TJDFT",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["court"] == "TJDFT"
        cleanup_holidays.append(data["id"])


class TestFilterHolidays:
    def test_year_filter(self, client, admin_headers, cleanup_holidays):
        a = client.post(
            URL,
            json={"date": "2098-05-01", "description": "A", "scope": "NATIONAL"},
            headers=admin_headers,
        )
        b = client.post(
            URL,
            json={"date": "2099-05-01", "description": "B", "scope": "NATIONAL"},
            headers=admin_headers,
        )
        cleanup_holidays.append(a.json()["data"]["id"])
        cleanup_holidays.append(b.json()["data"]["id"])

        response = client.get(f"{URL}?year=2099", headers=admin_headers)
        assert response.status_code == 200
        ids = [h["id"] for h in response.json()["data"]]
        assert b.json()["data"]["id"] in ids
        assert a.json()["data"]["id"] not in ids


class TestUpdateDelete:
    def test_admin_updates_description(self, client, admin_headers, cleanup_holidays):
        r = client.post(
            URL,
            json={"date": "2099-06-01", "description": "A", "scope": "NATIONAL"},
            headers=admin_headers,
        )
        hid = r.json()["data"]["id"]
        cleanup_holidays.append(hid)

        upd = client.patch(
            f"{URL}/{hid}",
            json={"description": "B"},
            headers=admin_headers,
        )
        assert upd.status_code == 200
        assert upd.json()["data"]["description"] == "B"

    def test_admin_deletes(self, client, admin_headers):
        r = client.post(
            URL,
            json={"date": "2099-07-01", "description": "ToDel", "scope": "NATIONAL"},
            headers=admin_headers,
        )
        hid = r.json()["data"]["id"]

        d = client.delete(f"{URL}/{hid}", headers=admin_headers)
        assert d.status_code == 204

        g = client.get(f"{URL}?year=2099", headers=admin_headers)
        ids = [h["id"] for h in g.json()["data"]]
        assert hid not in ids
