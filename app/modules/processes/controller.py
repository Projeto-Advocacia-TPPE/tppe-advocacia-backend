from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.clients.repository import ClientRepository
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
)
from app.modules.processes.service import ProcessService
from app.modules.users.model import User


class ProcessController:
    def __init__(self, db: Session) -> None:
        self.service = ProcessService(ProcessRepository(db), ClientRepository(db))

    def create_process(self, payload: ProcessCreate, created_by: User) -> Process:
        return self.service.create_process(payload, created_by=created_by)

    def get_process(self, process_id: int) -> Process:
        return self.service.get_process(process_id)

    def list_processes(
        self,
        client_id: int | None = None,
        status: ProcessStatus | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Process], int]:
        return self.service.list_processes(
            client_id=client_id,
            status=status,
            search=search,
            page=page,
            limit=limit,
        )

    def list_by_client(
        self, client_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[Process], int]:
        return self.service.list_by_client(client_id, page=page, limit=limit)

    def change_status(
        self,
        process_id: int,
        payload: ProcessStatusChange,
        current_user: User,
    ) -> tuple[Process, ProcessMovement]:
        return self.service.change_status(process_id, payload, current_user)

    def create_movement(
        self, process_id: int, payload: MovementCreate, created_by: User
    ) -> ProcessMovement:
        return self.service.create_movement(process_id, payload, created_by=created_by)

    def create_note(
        self,
        process_id: int,
        payload: ProcessNoteCreate,
        current_user: User,
    ) -> ProcessNote:
        return self.service.create_note(process_id, payload, current_user=current_user)

    def list_notes(
        self, process_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[ProcessNote], int]:
        return self.service.list_notes(process_id, page=page, limit=limit)

    def update_note(
        self,
        process_id: int,
        note_id: int,
        payload: ProcessNoteUpdate,
        current_user: User,
    ) -> ProcessNote:
        return self.service.update_note(
            process_id, note_id, payload, current_user=current_user
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
        return self.service.list_movements(
            process_id,
            source=source,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
        )
