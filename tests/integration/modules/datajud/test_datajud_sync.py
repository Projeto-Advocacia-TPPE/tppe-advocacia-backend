from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.modules.clients.repository import ClientRepository
from app.modules.datajud.fake_service import FakeDataJudService
from app.modules.datajud.protocol import DataJudClientError
from app.modules.datajud.schema import (
    DataJudBatchSyncRequest,
    DataJudMovement,
    DataJudSyncRequest,
)
from app.modules.datajud.service import DataJudService
from app.modules.external_api_logs.model import ExternalApiStatus
from app.modules.external_api_logs.repository import ExternalApiLogRepository
from app.modules.processes.model import MovementSource, Process
from app.modules.processes.repository import ProcessRepository
from app.shared.exceptions import DataJudUnavailableError


@pytest.fixture
def process_fixture(db: Session) -> Process:
    client = ClientRepository(db).create(name="Cliente DataJud", cpf="11122233355")
    return ProcessRepository(db).create(
        number="12345678920248262100",
        client_id=client.id,
        court="TJSP",
        tribunal_alias="tjsp",
        action_type="Ação Cível",
    )


def make_service(
    db: Session,
    datajud_client: FakeDataJudService,
    failure_notifier=None,
) -> DataJudService:
    return DataJudService(
        ProcessRepository(db),
        ExternalApiLogRepository(db),
        datajud_client,
        failure_notifier=failure_notifier,
    )


class TestDataJudSync:
    def test_sync_imports_system_movements_and_logs_success(
        self, db: Session, process_fixture
    ):
        service = make_service(
            db,
            FakeDataJudService(
                movements=[
                    DataJudMovement(
                        external_id="mov-1",
                        title="Conclusos para decisão",
                        description="Importado do DataJud",
                        occurred_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
                    )
                ]
            ),
        )

        result = service.sync_process_movements(
            process_fixture.id,
            DataJudSyncRequest(),
            actor_id=7,
        )

        assert result.imported_count == 1
        assert result.skipped_count == 0
        assert result.tribunal_alias == "tjsp"
        assert result.movements[0].source == MovementSource.SYSTEM
        assert result.movements[0].external_id == "mov-1"

        logs, total = ExternalApiLogRepository(db).list(process_id=process_fixture.id)
        assert total == 1
        assert logs[0].status == ExternalApiStatus.SUCCESS

    def test_sync_skips_existing_external_id(self, db: Session, process_fixture):
        service = make_service(
            db,
            FakeDataJudService(
                movements=[
                    DataJudMovement(
                        external_id="mov-duplicado",
                        title="Publicação",
                        occurred_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
                    )
                ]
            ),
        )

        first = service.sync_process_movements(
            process_fixture.id,
            DataJudSyncRequest(),
            actor_id=None,
        )
        second = service.sync_process_movements(
            process_fixture.id,
            DataJudSyncRequest(),
            actor_id=None,
        )

        assert first.imported_count == 1
        assert second.imported_count == 0
        assert second.skipped_count == 1

        movements, total = ProcessRepository(db).list_movements(process_fixture.id)
        assert total == 1
        assert movements[0].external_id == "mov-duplicado"

    def test_failure_logs_and_notifies(self, db: Session, process_fixture):
        notifier = MagicMock()
        service = make_service(
            db,
            FakeDataJudService(error=DataJudClientError("fora do ar", status_code=503)),
            failure_notifier=notifier,
        )

        with pytest.raises(DataJudUnavailableError):
            service.sync_process_movements(
                process_fixture.id,
                DataJudSyncRequest(),
                actor_id=7,
            )

        logs, total = ExternalApiLogRepository(db).list(process_id=process_fixture.id)
        assert total == 1
        assert logs[0].status == ExternalApiStatus.FAILURE
        assert logs[0].error_code == "DATAJUD_REQUEST_FAILED"
        notifier.notify_failure.assert_called_once_with(logs[0])

    def test_batch_continues_after_process_failure(self, db: Session, process_fixture):
        other = ProcessRepository(db).create(
            number="12345678920248262101",
            court="TJSP",
            tribunal_alias="tjsp",
            action_type="Ação Cível",
        )
        calls = 0

        class FlakyDataJudService(FakeDataJudService):
            def fetch_movements(self, process_number: str, tribunal_alias: str):
                nonlocal calls
                calls += 1
                if process_number == process_fixture.number:
                    raise DataJudClientError("fora do ar", status_code=503)
                return super().fetch_movements(process_number, tribunal_alias)

        service = make_service(db, FlakyDataJudService())

        result = service.sync_active_processes(
            payload=DataJudBatchSyncRequest(limit=10),
            actor_id=None,
        )

        assert calls == 2
        assert result.failure_count == 1
        assert result.success_count == 1
        assert {item.process_id for item in result.results} == {
            process_fixture.id,
            other.id,
        }
