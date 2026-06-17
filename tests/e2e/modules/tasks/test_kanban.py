import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.tasks.model import Task

TASKS_URL = "/api/v1/tasks"
KANBAN_URL = f"{TASKS_URL}/kanban"


@pytest.fixture(autouse=True)
def cleanup_tasks(db_session: Session):
    yield
    db_session.rollback()
    db_session.execute(delete(Task))
    db_session.commit()


def make_task(client, headers, title: str) -> dict:
    return client.post(TASKS_URL, json={"title": title}, headers=headers).json()["data"]


class TestGetKanban:
    def test_returns_401_without_token(self, client):
        assert client.get(KANBAN_URL).status_code == 401

    def test_returns_all_four_columns_when_empty(self, client, user_headers):
        body = client.get(KANBAN_URL, headers=user_headers).json()["data"]
        assert set(body.keys()) == {"TODO", "IN_PROGRESS", "BLOCKED", "DONE"}
        for column in body.values():
            assert column["items"] == []
            assert column["total"] == 0
            assert column["has_more"] is False

    def test_groups_by_status_and_orders_within_column(self, client, user_headers):
        a = make_task(client, user_headers, "a")
        b = make_task(client, user_headers, "b")
        client.patch(
            f"{TASKS_URL}/{b['id']}/move",
            json={"status": "DONE", "order": 0},
            headers=user_headers,
        )

        body = client.get(KANBAN_URL, headers=user_headers).json()["data"]

        assert [t["id"] for t in body["TODO"]["items"]] == [a["id"]]
        assert body["TODO"]["total"] == 1
        assert [t["id"] for t in body["DONE"]["items"]] == [b["id"]]
        assert body["DONE"]["total"] == 1

    def test_filters_by_assigned_to(
        self, client, user_headers, admin_headers, active_user
    ):
        client.post(
            TASKS_URL,
            json={"title": "mine", "assigned_to": active_user["id"]},
            headers=user_headers,
        )
        client.post(TASKS_URL, json={"title": "theirs"}, headers=admin_headers)

        body = client.get(
            f"{KANBAN_URL}?assigned_to={active_user['id']}",
            headers=user_headers,
        ).json()["data"]

        assert body["TODO"]["total"] == 1
        assert body["TODO"]["items"][0]["title"] == "mine"
