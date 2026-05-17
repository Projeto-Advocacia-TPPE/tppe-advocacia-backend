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
from app.modules.processes.schema import (
    MovementCreate,
    ProcessCreate,
    ProcessStatusChange,
)
from app.modules.users.model import User
from app.shared.exceptions import (
    ClientNotFoundError,
    ClientNotFoundForProcessError,
    ProcessNotFoundError,
    ProcessNumberAlreadyExistsError,
    ProcessStatusUnchangedError,
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
            process = self.repository.create_no_commit(
                number=payload.number,
                client_id=payload.client_id,
                court=payload.court,
                action_type=payload.action_type,
                opposing_party=payload.opposing_party,
                created_by=created_by.id,
            )
            self.repository.create_movement_no_commit(
                process_id=process.id,
                title="Processo cadastrado",
                description=None,
                occurred_at=datetime.now(timezone.utc),
                source=MovementSource.SYSTEM,
                created_by=created_by.id,
            )
            self.repository.db.commit()
        except IntegrityError as exc:
            self.repository.db.rollback()
            raise ProcessNumberAlreadyExistsError() from exc

        return self.repository.reload_with_client(process.id)

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

    def create_system_movement(
        self,
        process_id: int,
        title: str,
        description: str | None = None,
        created_by: int | None = None,
    ) -> ProcessMovement:
        self.get_process(process_id)
        return self.repository.create_movement(
            process_id=process_id,
            title=title,
            description=description,
            occurred_at=datetime.now(timezone.utc),
            source=MovementSource.SYSTEM,
            created_by=created_by,
        )

    def change_status(
        self,
        process_id: int,
        payload: ProcessStatusChange,
        current_user: User,
    ) -> tuple[Process, ProcessMovement]:
        process = self.get_process(process_id)

        if process.status == payload.status:
            raise ProcessStatusUnchangedError()

        previous = process.status
        try:
            self.repository.update_status_no_commit(
                process, payload.status, current_user.id
            )
            movement = self.repository.create_movement_no_commit(
                process_id=process.id,
                title=f"Status alterado: {previous.value} -> {payload.status.value}",
                description=payload.reason,
                occurred_at=datetime.now(timezone.utc),
                source=MovementSource.SYSTEM,
                created_by=current_user.id,
            )
            self.repository.db.commit()
        except Exception:
            self.repository.db.rollback()
            raise

        refreshed = self.repository.reload_with_client(process.id)
        reloaded_movement = self.repository.reload_movement(movement.id)
        return refreshed, reloaded_movement

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
