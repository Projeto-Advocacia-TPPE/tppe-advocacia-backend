"""E2E da integração Google Calendar.

No ambiente de teste o Google **não** está configurado (sem `GOOGLE_*` no
.env), então estes testes cobrem o comportamento desconectado/não-configurado.
O fluxo conectado (sync de eventos, OAuth) é coberto nos testes unitários do
service com o `FakeGoogleCalendarClient`.
"""

BASE = "/api/v1/integrations/google"


class TestAuthUrl:
    def test_requires_auth(self, client):
        assert client.get(f"{BASE}/auth-url").status_code in (401, 403)

    def test_returns_503_when_not_configured(self, client, user_headers):
        r = client.get(f"{BASE}/auth-url", headers=user_headers)
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "GOOGLE_NOT_CONFIGURED"


class TestStatus:
    def test_requires_auth(self, client):
        assert client.get(f"{BASE}/status").status_code in (401, 403)

    def test_reports_disconnected(self, client, user_headers):
        r = client.get(f"{BASE}/status", headers=user_headers)
        assert r.status_code == 200
        assert r.json()["data"]["connected"] is False
        assert r.json()["data"]["connected_at"] is None


class TestDisconnect:
    def test_requires_auth(self, client):
        assert client.delete(BASE).status_code in (401, 403)

    def test_idempotent_when_not_connected(self, client, user_headers):
        assert client.delete(BASE, headers=user_headers).status_code == 204


class TestSyncAll:
    def test_requires_auth(self, client):
        assert client.post(f"{BASE}/sync-all").status_code in (401, 403)

    def test_returns_503_when_not_configured(self, client, user_headers):
        r = client.post(f"{BASE}/sync-all", headers=user_headers)
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "GOOGLE_NOT_CONFIGURED"


class TestCallback:
    def test_redirects_to_error_when_params_missing(self, client):
        r = client.get(f"{BASE}/callback", follow_redirects=False)
        assert r.status_code == 302
        assert "google_calendar=error" in r.headers["location"]

    def test_redirects_to_error_on_google_error_param(self, client):
        r = client.get(
            f"{BASE}/callback",
            params={"error": "access_denied"},
            follow_redirects=False,
        )
        assert r.status_code == 302
        assert "google_calendar=error" in r.headers["location"]
