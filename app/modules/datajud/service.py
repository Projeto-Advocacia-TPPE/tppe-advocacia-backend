from __future__ import annotations

from datetime import datetime, timezone

from app.modules.datajud.protocol import (
    DataJudClient,
    DataJudClientError,
    DataJudConfigurationError,
    DataJudProcessNotFoundInResponseError,
)
from app.modules.datajud.schema import (
    DataJudBatchSyncItem,
    DataJudBatchSyncRequest,
    DataJudBatchSyncResponse,
    DataJudSyncRequest,
    DataJudSyncResponse,
)
from app.modules.external_api_logs.model import (
    ExternalApiOperation,
    ExternalApiProvider,
    ExternalApiStatus,
)
from app.modules.external_api_logs.notifier import ExternalApiFailureNotifier
from app.modules.external_api_logs.repository import ExternalApiLogRepository
from app.modules.processes.model import MovementSource
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.schema import MovementRead, format_cnj
from app.shared.exceptions import (
    AppException,
    DataJudNotConfiguredError,
    DataJudProcessNotFoundError,
    DataJudTribunalAliasRequiredError,
    DataJudUnavailableError,
    ProcessNotFoundError,
)
from app.shared.uow import unit_of_work


class DataJudService:
    def __init__(
        self,
        process_repository: ProcessRepository,
        log_repository: ExternalApiLogRepository,
        datajud_client: DataJudClient,
        failure_notifier: ExternalApiFailureNotifier | None = None,
    ) -> None:
        self.process_repository = process_repository
        self.log_repository = log_repository
        self.datajud_client = datajud_client
        self.failure_notifier = failure_notifier

    def sync_process_movements(
        self,
        process_id: int,
        payload: DataJudSyncRequest,
        actor_id: int | None,
    ) -> DataJudSyncResponse:
        process = self.process_repository.get_by_id(process_id)
        if process is None:
            raise ProcessNotFoundError()

        tribunal_alias = payload.tribunal_alias or process.tribunal_alias
        if tribunal_alias is None:
            raise DataJudTribunalAliasRequiredError()

        try:
            result = self.datajud_client.fetch_movements(
                process.number,
                tribunal_alias,
            )
        except DataJudConfigurationError as exc:
            self._log_failure(
                process_id=process.id,
                tribunal_alias=tribunal_alias,
                request_identifier=process.number,
                error_code="DATAJUD_NOT_CONFIGURED",
                error_message=str(exc),
                created_by=actor_id,
            )
            raise DataJudNotConfiguredError() from exc
        except DataJudProcessNotFoundInResponseError as exc:
            self._log_failure(
                process_id=process.id,
                tribunal_alias=tribunal_alias,
                request_identifier=process.number,
                http_status=exc.status_code,
                error_code="DATAJUD_PROCESS_NOT_FOUND",
                error_message=str(exc),
                created_by=actor_id,
            )
            raise DataJudProcessNotFoundError() from exc
        except DataJudClientError as exc:
            self._log_failure(
                process_id=process.id,
                tribunal_alias=tribunal_alias,
                request_identifier=process.number,
                http_status=exc.status_code,
                error_code="DATAJUD_REQUEST_FAILED",
                error_message=str(exc),
                created_by=actor_id,
            )
            raise DataJudUnavailableError() from exc

        imported_ids: list[int] = []
        skipped_count = result.skipped_count
        synced_at = datetime.now(timezone.utc)

        with unit_of_work(self.process_repository.db):
            for movement in result.movements:
                if self.process_repository.movement_external_id_exists(
                    process_id=process.id,
                    external_id=movement.external_id,
                ):
                    skipped_count += 1
                    continue

                imported = self.process_repository.create_movement_no_commit(
                    process_id=process.id,
                    title=movement.title,
                    description=movement.description,
                    occurred_at=movement.occurred_at,
                    source=MovementSource.SYSTEM,
                    external_id=movement.external_id,
                    created_by=actor_id,
                )
                imported_ids.append(imported.id)

            log = self.log_repository.create(
                provider=ExternalApiProvider.DATAJUD,
                operation=ExternalApiOperation.PROCESS_MOVEMENT_SYNC,
                status=ExternalApiStatus.SUCCESS,
                process_id=process.id,
                tribunal_alias=tribunal_alias,
                request_identifier=process.number,
                http_status=result.http_status,
                created_by=actor_id,
            )
            log_id = log.id

        imported_movements = [
            self.process_repository.reload_movement(movement_id)
            for movement_id in imported_ids
        ]
        return DataJudSyncResponse(
            process_id=process.id,
            process_number=format_cnj(process.number),
            tribunal_alias=tribunal_alias,
            imported_count=len(imported_ids),
            skipped_count=skipped_count,
            external_api_log_id=log_id,
            synced_at=synced_at,
            movements=[
                MovementRead.model_validate(movement)
                for movement in imported_movements
                if movement is not None
            ],
        )

    def sync_active_processes(
        self,
        payload: DataJudBatchSyncRequest,
        actor_id: int | None,
    ) -> DataJudBatchSyncResponse:
        processes, total = self.process_repository.list_active_for_datajud(
            tribunal_alias=payload.tribunal_alias,
            limit=payload.limit,
        )
        results: list[DataJudBatchSyncItem] = []
        imported_count = 0
        skipped_count = 0
        success_count = 0
        failure_count = 0
        synced_at = datetime.now(timezone.utc)

        for process in processes:
            process_tribunal_alias = payload.tribunal_alias or process.tribunal_alias
            try:
                sync_result = self.sync_process_movements(
                    process.id,
                    DataJudSyncRequest(tribunal_alias=payload.tribunal_alias),
                    actor_id,
                )
            except AppException as exc:
                failure_count += 1
                results.append(
                    DataJudBatchSyncItem(
                        process_id=process.id,
                        process_number=format_cnj(process.number),
                        tribunal_alias=process_tribunal_alias,
                        status="FAILURE",
                        error_code=exc.code,
                        error_message=exc.message,
                    )
                )
                continue

            success_count += 1
            imported_count += sync_result.imported_count
            skipped_count += sync_result.skipped_count
            results.append(
                DataJudBatchSyncItem(
                    process_id=sync_result.process_id,
                    process_number=sync_result.process_number,
                    tribunal_alias=sync_result.tribunal_alias,
                    status="SUCCESS",
                    imported_count=sync_result.imported_count,
                    skipped_count=sync_result.skipped_count,
                    external_api_log_id=sync_result.external_api_log_id,
                )
            )

        return DataJudBatchSyncResponse(
            tribunal_alias=payload.tribunal_alias,
            total_active_processes=total,
            processed_count=len(results),
            success_count=success_count,
            failure_count=failure_count,
            imported_count=imported_count,
            skipped_count=skipped_count,
            synced_at=synced_at,
            results=results,
        )

    def _log_failure(
        self,
        process_id: int,
        tribunal_alias: str,
        request_identifier: str,
        error_code: str,
        error_message: str,
        created_by: int | None,
        http_status: int | None = None,
    ) -> None:
        # O log de falha é uma transação separada da síntese principal:
        # mesmo quando a sincronização aborta, queremos a auditoria persistida.
        with unit_of_work(self.process_repository.db):
            log = self.log_repository.create(
                provider=ExternalApiProvider.DATAJUD,
                operation=ExternalApiOperation.PROCESS_MOVEMENT_SYNC,
                status=ExternalApiStatus.FAILURE,
                process_id=process_id,
                tribunal_alias=tribunal_alias,
                request_identifier=request_identifier,
                http_status=http_status,
                error_code=error_code,
                error_message=error_message[:500],
                created_by=created_by,
            )
        if self.failure_notifier is not None:
            self.failure_notifier.notify_failure(log)
