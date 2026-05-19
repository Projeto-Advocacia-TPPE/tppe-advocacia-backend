import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.tasks.model import Task

TASKS_URL = "/api/v1/tasks"


@pytest.fixture(autouse=True)
def cleanup_tasks(db_session: Session):
    yield
    db_session.rollback()
    db_session.execute(delete(Task))
    db_session.commit()


def make_task(client, headers, title: str) -> dict:
    return client.post(TASKS_URL, json={"title": title}, headers=headers).json()["data"]


class TestMoveTask:
    def test_returns_401_without_token(self, client):
        response = client.patch(
            f"{TASKS_URL}/1/move", json={"status": "DONE", "order": 0}
        )
        assert response.status_code == 401

    def test_move_within_column(self, client, user_headers):
        a = make_task(client, user_headers, "a")
        b = make_task(client, user_headers, "b")
        c = make_task(client, user_headers, "c")

        client.patch(
            f"{TASKS_URL}/{a['id']}/move",
            json={"status": "TODO", "order": 2},
            headers=user_headers,
        )

        items = client.get(TASKS_URL, headers=user_headers).json()["data"]
        by_id = {t["id"]: t["order"] for t in items}
        assert by_id[b["id"]] == 0
        assert by_id[c["id"]] == 1
        assert by_id[a["id"]] == 2

    def test_move_across_columns(self, client, user_headers):
        a = make_task(client, user_headers, "a")
        b = make_task(client, user_headers, "b")

        response = client.patch(
            f"{TASKS_URL}/{a['id']}/move",
            json={"status": "IN_PROGRESS", "order": 0},
            headers=user_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "IN_PROGRESS"
        assert data["order"] == 0

        refreshed_b = client.get(f"{TASKS_URL}/{b['id']}", headers=user_headers).json()[
            "data"
        ]
        assert refreshed_b["order"] == 0

    def test_move_to_done_sets_completed_at(self, client, user_headers):
        a = make_task(client, user_headers, "a")

        response = client.patch(
            f"{TASKS_URL}/{a['id']}/move",
            json={"status": "DONE", "order": 0},
            headers=user_headers,
        )
        assert response.json()["data"]["completed_at"] is not None

    def test_move_out_of_done_clears_completed_at(self, client, user_headers):
        a = make_task(client, user_headers, "a")
        client.patch(
            f"{TASKS_URL}/{a['id']}/move",
            json={"status": "DONE", "order": 0},
            headers=user_headers,
        )

        response = client.patch(
            f"{TASKS_URL}/{a['id']}/move",
            json={"status": "TODO", "order": 0},
            headers=user_headers,
        )
        assert response.json()["data"]["completed_at"] is None

    def test_invalid_status_returns_422(self, client, user_headers):
        a = make_task(client, user_headers, "a")
        response = client.patch(
            f"{TASKS_URL}/{a['id']}/move",
            json={"status": "INVALID", "order": 0},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_negative_order_returns_422(self, client, user_headers):
        a = make_task(client, user_headers, "a")
        response = client.patch(
            f"{TASKS_URL}/{a['id']}/move",
            json={"status": "TODO", "order": -1},
            headers=user_headers,
        )
        assert response.status_code == 422
