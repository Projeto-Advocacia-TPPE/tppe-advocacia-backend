import pytest

LOGIN_URL = "/api/v1/auth/login"


class TestLoginSuccess:
    def test_returns_200(self, client, active_user):
        response = client.post(
            LOGIN_URL, json={"email": active_user["email"], "password": active_user["password"]}
        )

        assert response.status_code == 200

    def test_success_is_true(self, client, active_user):
        response = client.post(
            LOGIN_URL, json={"email": active_user["email"], "password": active_user["password"]}
        )

        assert response.json()["success"] is True

    def test_returns_access_token(self, client, active_user):
        response = client.post(
            LOGIN_URL, json={"email": active_user["email"], "password": active_user["password"]}
        )

        assert "access_token" in response.json()["data"]
        assert len(response.json()["data"]["access_token"]) > 0

    def test_token_type_is_bearer(self, client, active_user):
        response = client.post(
            LOGIN_URL, json={"email": active_user["email"], "password": active_user["password"]}
        )

        assert response.json()["data"]["token_type"] == "bearer"


class TestLoginInvalidCredentials:
    def test_wrong_password_returns_401(self, client, active_user):
        response = client.post(
            LOGIN_URL, json={"email": active_user["email"], "password": "wrong_password"}
        )

        assert response.status_code == 401

    def test_wrong_password_returns_error_code(self, client, active_user):
        response = client.post(
            LOGIN_URL, json={"email": active_user["email"], "password": "wrong_password"}
        )

        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_unknown_email_returns_401(self, client):
        response = client.post(
            LOGIN_URL, json={"email": "nobody@test.com", "password": "any_password"}
        )

        assert response.status_code == 401

    def test_unknown_email_same_error_as_wrong_password(self, client, active_user):
        wrong_pass = client.post(
            LOGIN_URL, json={"email": active_user["email"], "password": "wrong"}
        )
        unknown = client.post(
            LOGIN_URL, json={"email": "nobody@test.com", "password": "wrong"}
        )

        assert wrong_pass.json()["error"]["code"] == unknown.json()["error"]["code"]


class TestLoginInactiveUser:
    def test_inactive_user_returns_403(self, client, inactive_user):
        response = client.post(
            LOGIN_URL,
            json={"email": inactive_user["email"], "password": inactive_user["password"]},
        )

        assert response.status_code == 403

    def test_inactive_user_returns_error_code(self, client, inactive_user):
        response = client.post(
            LOGIN_URL,
            json={"email": inactive_user["email"], "password": inactive_user["password"]},
        )

        assert response.json()["error"]["code"] == "INACTIVE_USER"


class TestLoginValidation:
    def test_missing_email_returns_422(self, client):
        response = client.post(LOGIN_URL, json={"password": "any_password"})

        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        response = client.post(LOGIN_URL, json={"email": "user@test.com"})

        assert response.status_code == 422

    def test_invalid_email_format_returns_422(self, client):
        response = client.post(
            LOGIN_URL, json={"email": "not-an-email", "password": "any_password"}
        )

        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        response = client.post(LOGIN_URL, json={})

        assert response.status_code == 422
