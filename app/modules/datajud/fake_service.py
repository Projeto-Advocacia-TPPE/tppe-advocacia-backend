from datetime import datetime, timezone

from app.modules.datajud.protocol import DataJudClientError
from app.modules.datajud.schema import DataJudFetchResult, DataJudMovement


class FakeDataJudService:
    def __init__(
        self,
        movements: list[DataJudMovement] | None = None,
        error: DataJudClientError | None = None,
        http_status: int | None = 200,
    ) -> None:
        self.movements = movements or [
            DataJudMovement(
                external_id="fake-movement-1",
                title="Movimento de teste",
                description="Importado do DataJud fake",
                occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        ]
        self.error = error
        self.http_status = http_status
        self.calls: list[tuple[str, str]] = []

    def fetch_movements(
        self,
        process_number: str,
        tribunal_alias: str,
    ) -> DataJudFetchResult:
        self.calls.append((process_number, tribunal_alias))
        if self.error is not None:
            raise self.error
        return DataJudFetchResult(
            movements=self.movements,
            skipped_count=0,
            http_status=self.http_status,
        )
