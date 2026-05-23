from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.external_api_logs.model import (
    ExternalApiLog,
    ExternalApiOperation,
    ExternalApiProvider,
    ExternalApiStatus,
)


class ExternalApiLogRepository:
    """Este repositório nunca comita. Operações de escrita usam db.add + db.flush
    e o Service que orquestra a transação fecha com unit_of_work."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        provider: ExternalApiProvider,
        operation: ExternalApiOperation,
        status: ExternalApiStatus,
        process_id: int | None = None,
        tribunal_alias: str | None = None,
        request_identifier: str | None = None,
        http_status: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        created_by: int | None = None,
    ) -> ExternalApiLog:
        log = ExternalApiLog(
            provider=provider,
            operation=operation,
            status=status,
            process_id=process_id,
            tribunal_alias=tribunal_alias,
            request_identifier=request_identifier,
            http_status=http_status,
            error_code=error_code,
            error_message=error_message,
            created_by=created_by,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list(
        self,
        provider: ExternalApiProvider | None = None,
        status: ExternalApiStatus | None = None,
        process_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ExternalApiLog], int]:
        statement = select(ExternalApiLog)

        if provider is not None:
            statement = statement.where(ExternalApiLog.provider == provider)
        if status is not None:
            statement = statement.where(ExternalApiLog.status == status)
        if process_id is not None:
            statement = statement.where(ExternalApiLog.process_id == process_id)
        if date_from is not None:
            statement = statement.where(ExternalApiLog.created_at >= date_from)
        if date_to is not None:
            statement = statement.where(ExternalApiLog.created_at <= date_to)

        total = (
            self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        )
        logs = list(
            self.db.scalars(
                statement.order_by(
                    ExternalApiLog.created_at.desc(),
                    ExternalApiLog.id.desc(),
                )
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()
        )
        return logs, total
