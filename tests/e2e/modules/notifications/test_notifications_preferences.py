import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.notifications.model import NotificationPreference

PREFERENCES_URL = "/api/v1/notifications/preferences"


@pytest.fixture(autouse=True)
def cleanup_preferences(db_session: Session, active_user, admin_user):
    yield
    db_session.execute(
        delete(NotificationPreference).where(
            NotificationPreference.user_id.in_([active_user["id"], admin_user["id"]])
        )
    )
    db_session.commit()


class TestGetPreferences:
    def test_returns_401_without_token(self, client):
        response = client.get(PREFERENCES_URL)

        assert response.status_code == 401

    def test_returns_200_for_authenticated_user(self, client, user_headers):
        response = client.get(PREFERENCES_URL, headers=user_headers)

        assert response.status_code == 200

    def test_returns_all_event_types_with_default_true(self, client, user_headers):
        response = client.get(PREFERENCES_URL, headers=user_headers)
        prefs = response.json()["data"]["preferences"]

        assert prefs == {
            "PROCESS_MOVEMENT_CREATED": True,
            "PROCESS_STATUS_CHANGED": True,
            "LEAD_ASSIGNED": True,
            "TASK_ASSIGNED": True,
            "DEADLINE_APPROACHING": True,
            "DEADLINE_EXPIRED": True,
        }


class TestUpdatePreferences:
    def test_returns_401_without_token(self, client):
        response = client.patch(
            PREFERENCES_URL, json={"preferences": {"LEAD_ASSIGNED": False}}
        )

        assert response.status_code == 401

    def test_updates_single_preference(self, client, user_headers):
        response = client.patch(
            PREFERENCES_URL,
            json={"preferences": {"LEAD_ASSIGNED": False}},
            headers=user_headers,
        )

        assert response.status_code == 200
        prefs = response.json()["data"]["preferences"]
        assert prefs["LEAD_ASSIGNED"] is False
        assert prefs["PROCESS_MOVEMENT_CREATED"] is True

    def test_persists_across_requests(self, client, user_headers):
        client.patch(
            PREFERENCES_URL,
            json={"preferences": {"TASK_ASSIGNED": False}},
            headers=user_headers,
        )

        response = client.get(PREFERENCES_URL, headers=user_headers)
        prefs = response.json()["data"]["preferences"]

        assert prefs["TASK_ASSIGNED"] is False

    def test_partial_update_preserves_other_values(self, client, user_headers):
        client.patch(
            PREFERENCES_URL,
            json={
                "preferences": {
                    "LEAD_ASSIGNED": False,
                    "TASK_ASSIGNED": False,
                }
            },
            headers=user_headers,
        )
        client.patch(
            PREFERENCES_URL,
            json={"preferences": {"LEAD_ASSIGNED": True}},
            headers=user_headers,
        )

        response = client.get(PREFERENCES_URL, headers=user_headers)
        prefs = response.json()["data"]["preferences"]

        assert prefs["LEAD_ASSIGNED"] is True
        assert prefs["TASK_ASSIGNED"] is False

    def test_invalid_event_type_returns_422(self, client, user_headers):
        response = client.patch(
            PREFERENCES_URL,
            json={"preferences": {"INVALID_EVENT": False}},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_empty_preferences_returns_422(self, client, user_headers):
        response = client.patch(
            PREFERENCES_URL, json={"preferences": {}}, headers=user_headers
        )

        assert response.status_code == 422
