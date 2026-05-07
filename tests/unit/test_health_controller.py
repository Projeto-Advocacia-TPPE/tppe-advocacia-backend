from unittest.mock import patch

from app.controllers.health_controller import HealthController


@patch("app.controllers.health_controller.check_database_connection")
class TestHealthControllerStatus:
    def test_status_ok_when_db_connected(self, mock_db):
        mock_db.return_value = True

        result = HealthController().get_status()

        assert result.status == "ok"

    def test_status_degraded_when_db_unavailable(self, mock_db):
        mock_db.return_value = False

        result = HealthController().get_status()

        assert result.status == "degraded"

    def test_database_connected_when_db_up(self, mock_db):
        mock_db.return_value = True

        result = HealthController().get_status()

        assert result.database == "connected"

    def test_database_unavailable_when_db_down(self, mock_db):
        mock_db.return_value = False

        result = HealthController().get_status()

        assert result.database == "unavailable"

    def test_returns_app_name_from_settings(self, mock_db):
        mock_db.return_value = True

        result = HealthController().get_status()

        assert isinstance(result.app_name, str)
        assert len(result.app_name) > 0

    def test_returns_version_from_settings(self, mock_db):
        mock_db.return_value = True

        result = HealthController().get_status()

        assert isinstance(result.version, str)
        assert len(result.version) > 0
