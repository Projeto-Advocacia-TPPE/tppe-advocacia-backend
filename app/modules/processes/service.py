from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import (
    MovementSource,
    Process,
    ProcessMovement,
    ProcessStatus,
)
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.schema import MovementCreate, ProcessCreate
from app.modules.users.model import User
from app.shared.exceptions import (
    ClientNotFoundError,
    ClientNotFoundForProcessError,
    ProcessNotFoundError,
    ProcessNumberAlreadyExistsError,
)


class ProcessService:
    def __init__(
        self, repository: ProcessRepository, client_repository: ClientRepository
    ) -> None:
        self.repository = repository
        self.client_repository = client_repository

    def create_process(self, payload: ProcessCreate, created_by: User) -> Process:
        if (
            payload.client_id is not None
            and self.client_repository.get_by_id(payload.client_id) is None
        ):
            raise ClientNotFoundForProcessError()

        try:
            return self.repository.create(
                number=payload.number,
                client_id=payload.client_id,
                court=payload.court,
                action_type=payload.action_type,
                opposing_party=payload.opposing_party,
                created_by=created_by.id,
            )
        except IntegrityError as exc:
            self.repository.db.rollback()
            raise ProcessNumberAlreadyExistsError() from exc

    def get_process(self, process_id: int) -> Process:
        process = self.repository.get_by_id(process_id)
        if process is None:
            raise ProcessNotFoundError()
        return process

    def list_processes(
        self,
        client_id: int | None = None,
        status: ProcessStatus | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Process], int]:
        return self.repository.list(
            client_id=client_id,
            status=status,
            search=search,
            page=page,
            limit=limit,
        )

    def list_by_client(
        self, client_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[Process], int]:
        if self.client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError()
        return self.repository.list_by_client(
            client_id=client_id, page=page, limit=limit
        )

    def create_movement(
        self, process_id: int, payload: MovementCreate, created_by: User
    ) -> ProcessMovement:
        self.get_process(process_id)
        occurred_at = payload.occurred_at or datetime.now(timezone.utc)
        return self.repository.create_movement(
            process_id=process_id,
            title=payload.title,
            description=payload.description,
            occurred_at=occurred_at,
            source=MovementSource.MANUAL,
            created_by=created_by.id,
        )

    def list_movements(
        self,
        process_id: int,
        source: MovementSource | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ProcessMovement], int]:
        self.get_process(process_id)
        return self.repository.list_movements(
            process_id=process_id,
            source=source,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
        )
