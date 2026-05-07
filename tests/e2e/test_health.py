from unittest.mock import patch

HEALTH_URL = "/api/v1/health"
DB_CHECK = "app.controllers.health_controller.check_database_connection"


class TestHealthEndpointDBUp:
    def test_returns_200(self, client):
        response = client.get(HEALTH_URL)

        assert response.status_code == 200

    def test_success_is_true(self, client):
        response = client.get(HEALTH_URL)

        assert response.json()["success"] is True

    def test_status_is_ok(self, client):
        response = client.get(HEALTH_URL)

        assert response.json()["data"]["status"] == "ok"

    def test_database_is_connected(self, client):
        response = client.get(HEALTH_URL)

        assert response.json()["data"]["database"] == "connected"

    def test_response_has_app_name(self, client):
        response = client.get(HEALTH_URL)

        assert isinstance(response.json()["data"]["app_name"], str)

    def test_response_has_version(self, client):
        response = client.get(HEALTH_URL)

        assert isinstance(response.json()["data"]["version"], str)


class TestHealthEndpointDBDown:
    def test_returns_200_even_when_db_down(self, client):
        with patch(DB_CHECK, return_value=False):
            response = client.get(HEALTH_URL)

        assert response.status_code == 200

    def test_status_is_degraded(self, client):
        with patch(DB_CHECK, return_value=False):
            response = client.get(HEALTH_URL)

        assert response.json()["data"]["status"] == "degraded"

    def test_database_is_unavailable(self, client):
        with patch(DB_CHECK, return_value=False):
            response = client.get(HEALTH_URL)

        assert response.json()["data"]["database"] == "unavailable"

    def test_success_is_still_true(self, client):
        with patch(DB_CHECK, return_value=False):
            response = client.get(HEALTH_URL)

        assert response.json()["success"] is True
