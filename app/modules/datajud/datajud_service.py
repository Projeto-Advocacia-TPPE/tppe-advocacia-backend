from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config.settings import get_settings
from app.modules.datajud.protocol import (
    DataJudClientError,
    DataJudConfigurationError,
    DataJudProcessNotFoundInResponseError,
)
from app.modules.datajud.schema import DataJudFetchResult, DataJudMovement
from app.shared.datajud import normalize_datajud_tribunal_alias


class DataJudApiService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.datajud_api_key
        self.base_url = (
            base_url if base_url is not None else settings.datajud_base_url
        ).rstrip("/")
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.datajud_timeout_seconds
        )
        self.max_retries = max(
            0,
            max_retries if max_retries is not None else settings.datajud_max_retries,
        )
        self.retry_backoff_seconds = max(
            0,
            retry_backoff_seconds
            if retry_backoff_seconds is not None
            else settings.datajud_retry_backoff_seconds,
        )
        self.sleep = sleep

    def fetch_movements(
        self,
        process_number: str,
        tribunal_alias: str,
    ) -> DataJudFetchResult:
        if not self.api_key:
            raise DataJudConfigurationError("DATAJUD_API_KEY is not configured")

        alias = normalize_datajud_tribunal_alias(tribunal_alias)
        if alias is None:
            raise DataJudConfigurationError("DataJud tribunal alias is required")

        response = self._post_search(alias, process_number)
        try:
            payload = response.json()
        except ValueError as exc:
            raise DataJudClientError(
                "DataJud returned an invalid JSON response",
                status_code=response.status_code,
            ) from exc

        source = self._extract_source(payload, process_number)
        movements, skipped_count = self._parse_movements(
            process_number,
            source.get("movimentos", []),
        )
        return DataJudFetchResult(
            movements=movements,
            skipped_count=skipped_count,
            http_status=response.status_code,
        )

    def _post_search(self, tribunal_alias: str, process_number: str) -> httpx.Response:
        url = f"{self.base_url}/api_publica_{tribunal_alias}/_search"
        payload = {
            "query": {"match": {"numeroProcesso": process_number}},
            "size": 1,
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"APIKey {self.api_key}"},
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                if self._should_retry_status(exc.response.status_code, attempt):
                    self._sleep_before_retry(attempt)
                    continue
                raise DataJudClientError(
                    "DataJud returned an error response",
                    status_code=exc.response.status_code,
                ) from exc
            except httpx.RequestError as exc:
                if self._has_attempts_left(attempt):
                    self._sleep_before_retry(attempt)
                    continue
                raise DataJudClientError("DataJud request failed") from exc

        raise DataJudClientError("DataJud request failed")

    def _extract_source(
        self,
        payload: dict[str, Any],
        process_number: str,
    ) -> dict[str, Any]:
        hits = payload.get("hits", {}).get("hits", [])
        for hit in hits:
            source = hit.get("_source", {})
            if source.get("numeroProcesso") == process_number:
                return source
        raise DataJudProcessNotFoundInResponseError(
            "DataJud did not return a hit for this process"
        )

    def _parse_movements(
        self,
        process_number: str,
        raw_movements: object,
    ) -> tuple[list[DataJudMovement], int]:
        if not isinstance(raw_movements, list):
            return [], 0

        movements: list[DataJudMovement] = []
        skipped_count = 0
        for raw in raw_movements:
            parsed = self._parse_movement(process_number, raw)
            if parsed is None:
                skipped_count += 1
                continue
            movements.append(parsed)
        return movements, skipped_count

    def _parse_movement(
        self,
        process_number: str,
        raw: object,
    ) -> DataJudMovement | None:
        if not isinstance(raw, dict):
            return None

        occurred_at = self._parse_datetime(raw.get("dataHora"))
        if occurred_at is None:
            return None

        code = raw.get("codigo")
        fallback_title = f"Movimento {code}" if code is not None else "Movimento"
        title = str(raw.get("nome") or fallback_title)
        return DataJudMovement(
            external_id=self._external_id(process_number, raw),
            title=self._truncate(title, 150),
            description=self._build_description(raw),
            occurred_at=occurred_at,
        )

    def _external_id(self, process_number: str, movement: dict[str, Any]) -> str:
        explicit_id = (
            movement.get("id")
            or movement.get("identificadorMovimento")
            or movement.get("sequencia")
        )
        if explicit_id is not None:
            return self._truncate(str(explicit_id), 64)

        raw_key = {
            "process_number": process_number,
            "dataHora": movement.get("dataHora"),
            "codigo": movement.get("codigo"),
            "nome": movement.get("nome"),
            "complementosTabelados": movement.get("complementosTabelados"),
        }
        encoded = json.dumps(raw_key, sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _build_description(self, movement: dict[str, Any]) -> str:
        parts = ["Importado do DataJud"]

        if movement.get("codigo") is not None:
            parts.append(f"Codigo TPU: {movement['codigo']}")

        judging_body = movement.get("orgaoJulgador")
        if isinstance(judging_body, dict):
            body_name = judging_body.get("nomeOrgao")
            if body_name:
                parts.append(f"Orgao julgador: {body_name}")

        complements = movement.get("complementosTabelados")
        if isinstance(complements, list):
            complement_names = [
                str(item.get("nome"))
                for item in complements
                if isinstance(item, dict) and item.get("nome")
            ]
            if complement_names:
                parts.append("Complementos: " + ", ".join(complement_names[:3]))

        return self._truncate("; ".join(parts), 5000)

    def _parse_datetime(self, value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _truncate(self, value: str, max_length: int) -> str:
        return value if len(value) <= max_length else value[:max_length]

    def _should_retry_status(self, status_code: int, attempt: int) -> bool:
        return (status_code == 429 or status_code >= 500) and self._has_attempts_left(
            attempt
        )

    def _has_attempts_left(self, attempt: int) -> bool:
        return attempt < self.max_retries

    def _sleep_before_retry(self, attempt: int) -> None:
        delay = self.retry_backoff_seconds * (attempt + 1)
        if delay > 0:
            self.sleep(delay)
