import pytest
from sqlalchemy import delete, select

from app.modules.audit_logs.model import AuditAction, AuditLog
from app.modules.users.model import User

AUDIT_LOGS_URL = "/api/v1/audit-logs"
USERS_URL = "/api/v1/users"


@pytest.fixture
def created_user_with_audit(client, admin_headers, db_session):
    response = client.post(
        USERS_URL,
        json={"name": "Audit Test User", "email": "e2e_audit_create@test.com"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    user_id = response.json()["data"]["id"]
    yield user_id
    db_session.execute(delete(AuditLog).where(AuditLog.target_user_id == user_id))
    db_session.execute(delete(User).where(User.id == user_id))
    db_session.commit()


@pytest.fixture
def deactivated_user_with_audit(client, admin_headers, db_session):
    create_resp = client.post(
        USERS_URL,
        json={
            "name": "Audit Deactivate User",
            "email": "e2e_audit_deactivate@test.com",
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["data"]["id"]

    client.patch(
        f"{USERS_URL}/{user_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    yield user_id
    db_session.execute(delete(AuditLog).where(AuditLog.target_user_id == user_id))
    db_session.execute(delete(User).where(User.id == user_id))
    db_session.commit()


class TestListAuditLogs:
    def test_returns_200(self, client, admin_headers):
        response = client.get(AUDIT_LOGS_URL, headers=admin_headers)

        assert response.status_code == 200

    def test_returns_401_without_token(self, client):
        response = client.get(AUDIT_LOGS_URL)

        assert response.status_code == 401

    def test_returns_403_with_user_token(self, client, user_headers):
        response = client.get(AUDIT_LOGS_URL, headers=user_headers)

        assert response.status_code == 403

    def test_success_is_true(self, client, admin_headers):
        response = client.get(AUDIT_LOGS_URL, headers=admin_headers)

        assert response.json()["success"] is True

    def test_returns_paginated_structure(self, client, admin_headers):
        response = client.get(AUDIT_LOGS_URL, headers=admin_headers)
        meta = response.json()["meta"]

        assert "total" in meta
        assert "page" in meta
        assert "limit" in meta
        assert "pages" in meta

    def test_pagination_respects_limit(self, client, admin_headers):
        response = client.get(f"{AUDIT_LOGS_URL}?limit=1", headers=admin_headers)

        assert len(response.json()["data"]) <= 1

    def test_invalid_limit_returns_422(self, client, admin_headers):
        response = client.get(f"{AUDIT_LOGS_URL}?limit=0", headers=admin_headers)

        assert response.status_code == 422


class TestAuditLogIntegration:
    def test_create_user_generates_user_created_log(
        self, client, admin_headers, created_user_with_audit
    ):
        user_id = created_user_with_audit

        response = client.get(
            f"{AUDIT_LOGS_URL}?action=USER_CREATED", headers=admin_headers
        )
        logs = response.json()["data"]

        assert any(log["target_user_id"] == user_id for log in logs)

    def test_user_created_log_has_correct_fields(
        self, client, admin_headers, created_user_with_audit
    ):
        user_id = created_user_with_audit

        response = client.get(
            f"{AUDIT_LOGS_URL}?action=USER_CREATED", headers=admin_headers
        )
        log = next(
            entry
            for entry in response.json()["data"]
            if entry["target_user_id"] == user_id
        )

        assert log["action"] == "USER_CREATED"
        assert log["target_user_email"] == "e2e_audit_create@test.com"
        assert log["target_user_name"] == "Audit Test User"
        assert log["performed_by_id"] is not None

    def test_deactivate_user_generates_user_deactivated_log(
        self, client, admin_headers, deactivated_user_with_audit
    ):
        user_id = deactivated_user_with_audit

        response = client.get(
            f"{AUDIT_LOGS_URL}?action=USER_DEACTIVATED", headers=admin_headers
        )
        logs = response.json()["data"]

        assert any(log["target_user_id"] == user_id for log in logs)

    def test_filter_by_action_returns_only_matching_records(
        self, client, admin_headers, created_user_with_audit
    ):
        response = client.get(
            f"{AUDIT_LOGS_URL}?action=USER_CREATED", headers=admin_headers
        )

        assert all(log["action"] == "USER_CREATED" for log in response.json()["data"])

    def test_updating_name_generates_user_updated_log(
        self, client, admin_headers, created_user_with_audit, db_session
    ):
        user_id = created_user_with_audit

        client.patch(
            f"{USERS_URL}/{user_id}",
            json={"name": "Updated Name"},
            headers=admin_headers,
        )

        updated_logs = (
            db_session.execute(
                select(AuditLog).where(
                    AuditLog.target_user_id == user_id,
                    AuditLog.action == AuditAction.USER_UPDATED,
                )
            )
            .scalars()
            .all()
        )

        assert len(updated_logs) == 1

    def test_deactivation_does_not_generate_user_updated_log(
        self, client, admin_headers, created_user_with_audit, db_session
    ):
        user_id = created_user_with_audit

        client.patch(
            f"{USERS_URL}/{user_id}",
            json={"is_active": False},
            headers=admin_headers,
        )

        updated_logs = (
            db_session.execute(
                select(AuditLog).where(
                    AuditLog.target_user_id == user_id,
                    AuditLog.action == AuditAction.USER_UPDATED,
                )
            )
            .scalars()
            .all()
        )

        assert len(updated_logs) == 0
