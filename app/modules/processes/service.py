from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.modules.clients.repository import ClientRepository
from app.modules.notifications.schema import EventType
from app.modules.notifications.service import NotificationService
from app.modules.processes.model import (
    MovementSource,
    Process,
    ProcessMovement,
    ProcessNote,
    ProcessStatus,
)
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.schema import (
    MovementCreate,
    ProcessCreate,
    ProcessNoteCreate,
    ProcessNoteUpdate,
    ProcessStatusChange,
    format_cnj,
)
from app.modules.users.model import User
from app.shared.exceptions import (
    ClientNotFoundError,
    ClientNotFoundForProcessError,
    ForbiddenError,
    ProcessNoteNotFoundError,
    ProcessNotFoundError,
    ProcessNumberAlreadyExistsError,
    ProcessStatusUnchangedError,
)
from app.shared.types import Role
from app.shared.uow import unit_of_work


class ProcessService:
    def __init__(
        self,
        repository: ProcessRepository,
        client_repository: ClientRepository,
        notifications: NotificationService | None = None,
    ) -> None:
        self.repository = repository
        self.client_repository = client_repository
        self.notifications = notifications

    def create_process(self, payload: ProcessCreate, created_by: User) -> Process:
        if (
            payload.client_id is not None
            and self.client_repository.get_by_id(payload.client_id) is None
        ):
            raise ClientNotFoundForProcessError()

        try:
            with unit_of_work(self.repository.db):
                process = self.repository.create_no_commit(
                    number=payload.number,
                    client_id=payload.client_id,
                    court=payload.court,
                    tribunal_alias=payload.tribunal_alias,
                    action_type=payload.action_type,
                    opposing_party=payload.opposing_party,
                    created_by=created_by.id,
                )
                initial_movement = self.repository.create_movement_no_commit(
                    process_id=process.id,
                    title="Processo cadastrado",
                    description=None,
                    occurred_at=datetime.now(timezone.utc),
                    source=MovementSource.SYSTEM,
                    created_by=created_by.id,
                )
        except IntegrityError as exc:
            raise ProcessNumberAlreadyExistsError() from exc

        refreshed = self.repository.reload_with_client(process.id)
        self._notify_movement(refreshed, initial_movement, actor_id=created_by.id)
        return refreshed

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
        process = self.get_process(process_id)
        occurred_at = payload.occurred_at or datetime.now(timezone.utc)
        with unit_of_work(self.repository.db):
            movement = self.repository.create_movement(
                process_id=process_id,
                title=payload.title,
                description=payload.description,
                occurred_at=occurred_at,
                source=MovementSource.MANUAL,
                created_by=created_by.id,
            )
        self._notify_movement(process, movement, actor_id=created_by.id)
        return movement

    def create_system_movement(
        self,
        process_id: int,
        title: str,
        description: str | None = None,
        external_id: str | None = None,
        created_by: int | None = None,
    ) -> ProcessMovement:
        process = self.get_process(process_id)
        with unit_of_work(self.repository.db):
            movement = self.repository.create_movement(
                process_id=process_id,
                title=title,
                description=description,
                occurred_at=datetime.now(timezone.utc),
                source=MovementSource.SYSTEM,
                external_id=external_id,
                created_by=created_by,
            )
        self._notify_movement(process, movement, actor_id=created_by)
        return movement

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
        with unit_of_work(self.repository.db):
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

        refreshed = self.repository.reload_with_client(process.id)
        reloaded_movement = self.repository.reload_movement(movement.id)
        self._notify_status_change(
            refreshed,
            actor_id=current_user.id,
            previous=previous,
            new_status=payload.status,
            reason=payload.reason,
        )
        return refreshed, reloaded_movement

    def create_note(
        self,
        process_id: int,
        payload: ProcessNoteCreate,
        current_user: User,
    ) -> ProcessNote:
        self.get_process(process_id)
        with unit_of_work(self.repository.db):
            note = self.repository.create_note(
                process_id=process_id,
                created_by=current_user.id,
                content=payload.content,
            )
        return note

    def list_notes(
        self, process_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[ProcessNote], int]:
        self.get_process(process_id)
        return self.repository.list_notes_by_process(
            process_id=process_id, page=page, limit=limit
        )

    def update_note(
        self,
        process_id: int,
        note_id: int,
        payload: ProcessNoteUpdate,
        current_user: User,
    ) -> ProcessNote:
        self.get_process(process_id)
        note = self.repository.get_note_by_id(note_id=note_id, process_id=process_id)

        if note is None:
            raise ProcessNoteNotFoundError()

        if note.created_by != current_user.id and current_user.role != Role.ADMIN:
            raise ForbiddenError()

        with unit_of_work(self.repository.db):
            updated = self.repository.update_note(
                note=note, content=payload.content, updated_by=current_user.id
            )
        return updated

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

    def _recipients_for(self, process: Process) -> set[int]:
        recipients: set[int] = set()
        if process.created_by is not None:
            recipients.add(process.created_by)
        return recipients

    def _notify_movement(
        self,
        process: Process,
        movement: ProcessMovement,
        actor_id: int | None,
    ) -> None:
        if self.notifications is None:
            return
        payload = {
            "process_id": process.id,
            "process_number": format_cnj(process.number),
            "title": movement.title,
            "description": movement.description,
            "occurred_at": movement.occurred_at.isoformat()
            if movement.occurred_at
            else None,
        }
        for user_id in self._recipients_for(process):
            if user_id == actor_id:
                continue
            self.notifications.notify(
                user_id=user_id,
                event_type=EventType.PROCESS_MOVEMENT_CREATED,
                payload=payload,
            )

    def _notify_status_change(
        self,
        process: Process,
        actor_id: int | None,
        previous: ProcessStatus,
        new_status: ProcessStatus,
        reason: str | None,
    ) -> None:
        if self.notifications is None:
            return
        payload = {
            "process_id": process.id,
            "process_number": format_cnj(process.number),
            "previous_status": previous.value,
            "new_status": new_status.value,
            "reason": reason,
        }
        for user_id in self._recipients_for(process):
            if user_id == actor_id:
                continue
            self.notifications.notify(
                user_id=user_id,
                event_type=EventType.PROCESS_STATUS_CHANGED,
                payload=payload,
            )
