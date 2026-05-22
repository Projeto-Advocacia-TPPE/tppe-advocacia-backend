from __future__ import annotations

import httpx
import pytest

from app.modules.datajud.datajud_service import DataJudApiService
from app.modules.datajud.protocol import (
    DataJudClientError,
    DataJudConfigurationError,
)


def make_response(status_code: int, payload: dict) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("POST", "https://datajud.test/_search"),
    )


def datajud_payload(movements: list[dict]) -> dict:
    return {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "numeroProcesso": "12345678920248260100",
                        "movimentos": movements,
                    }
                }
            ]
        }
    }


class TestDataJudApiService:
    def test_requires_api_key(self):
        service = DataJudApiService(api_key="")

        with pytest.raises(DataJudConfigurationError):
            service.fetch_movements("12345678920248260100", "tjsp")

    def test_fetches_and_parses_movements(self, monkeypatch):
        captured = {}

        def fake_post(url, json, headers, timeout):
            captured.update(
                {
                    "url": url,
                    "json": json,
                    "headers": headers,
                    "timeout": timeout,
                }
            )
            return make_response(
                200,
                datajud_payload(
                    [
                        {
                            "codigo": 1,
                            "nome": "Conclusos para decisão",
                            "dataHora": "2026-05-20T10:00:00Z",
                            "orgaoJulgador": {"nomeOrgao": "1ª Vara Cível"},
                        },
                        {"codigo": 2, "nome": "Sem data"},
                    ]
                ),
            )

        monkeypatch.setattr(httpx, "post", fake_post)

        service = DataJudApiService(
            api_key="secret",
            base_url="https://datajud.test",
            timeout_seconds=3,
        )
        result = service.fetch_movements("12345678920248260100", "TJSP")

        assert captured["url"] == "https://datajud.test/api_publica_tjsp/_search"
        assert captured["headers"] == {"Authorization": "APIKey secret"}
        assert captured["json"]["query"]["match"]["numeroProcesso"] == (
            "12345678920248260100"
        )
        assert result.http_status == 200
        assert result.skipped_count == 1
        assert len(result.movements) == 1
        assert result.movements[0].title == "Conclusos para decisão"
        assert result.movements[0].external_id
        assert "Orgao julgador" in result.movements[0].description

    def test_retries_transient_status(self, monkeypatch):
        responses = [
            make_response(500, {"error": "temporary"}),
            make_response(200, datajud_payload([])),
        ]
        calls = []

        def fake_post(*args, **kwargs):
            calls.append((args, kwargs))
            response = responses.pop(0)
            response.raise_for_status()
            return response

        monkeypatch.setattr(httpx, "post", fake_post)

        service = DataJudApiService(
            api_key="secret",
            base_url="https://datajud.test",
            max_retries=1,
            retry_backoff_seconds=0,
        )

        result = service.fetch_movements("12345678920248260100", "tjsp")

        assert result.movements == []
        assert len(calls) == 2

    def test_raises_client_error_after_status_failure(self, monkeypatch):
        def fake_post(*args, **kwargs):
            response = make_response(503, {"error": "down"})
            response.raise_for_status()
            return response

        monkeypatch.setattr(httpx, "post", fake_post)
        service = DataJudApiService(
            api_key="secret",
            base_url="https://datajud.test",
            max_retries=0,
        )

        with pytest.raises(DataJudClientError) as exc:
            service.fetch_movements("12345678920248260100", "tjsp")

        assert exc.value.status_code == 503
