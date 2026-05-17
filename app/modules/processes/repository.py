from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.processes.model import (
    MovementSource,
    Process,
    ProcessMovement,
    ProcessNote,
    ProcessStatus,
)


class ProcessRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _query(self):
        return select(Process).options(joinedload(Process.client))

    def create_no_commit(
        self,
        number: str,
        court: str,
        action_type: str,
        client_id: int | None = None,
        opposing_party: str | None = None,
        created_by: int | None = None,
    ) -> Process:
        process = Process(
            number=number,
            client_id=client_id,
            court=court,
            action_type=action_type,
            opposing_party=opposing_party,
            status=ProcessStatus.ATIVO,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(process)
        self.db.flush()
        return process

    def create(
        self,
        number: str,
        court: str,
        action_type: str,
        client_id: int | None = None,
        opposing_party: str | None = None,
        created_by: int | None = None,
    ) -> Process:
        process = self.create_no_commit(
            number=number,
            court=court,
            action_type=action_type,
            client_id=client_id,
            opposing_party=opposing_party,
            created_by=created_by,
        )
        self.db.commit()
        return self.db.scalars(self._query().where(Process.id == process.id)).first()

    def update_status_no_commit(
        self, process: Process, new_status: ProcessStatus, updated_by: int | None
    ) -> Process:
        process.status = new_status
        process.updated_by = updated_by
        self.db.add(process)
        self.db.flush()
        return process

    def reload_with_client(self, process_id: int) -> Process | None:
        return self.db.scalars(self._query().where(Process.id == process_id)).first()

    def get_by_id(self, process_id: int) -> Process | None:
        return self.db.scalars(self._query().where(Process.id == process_id)).first()

    def get_by_number(self, number: str) -> Process | None:
        return self.db.scalars(self._query().where(Process.number == number)).first()

    def list(
        self,
        client_id: int | None = None,
        status: ProcessStatus | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Process], int]:
        base = select(Process)

        if client_id is not None:
            base = base.where(Process.client_id == client_id)
        if status is not None:
            base = base.where(Process.status == status)
        if search:
            term = f"%{search.lower()}%"
            base = base.where(
                or_(
                    func.lower(Process.number).like(term),
                    func.lower(Process.action_type).like(term),
                )
            )

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.options(joinedload(Process.client))
                .order_by(Process.created_at.desc(), Process.id.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
            .unique()
            .all()
        )
        return items, total

    def list_by_client(
        self, client_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[Process], int]:
        return self.list(client_id=client_id, page=page, limit=limit)

    def _movement_query(self):
        return select(ProcessMovement).options(joinedload(ProcessMovement.creator))

    def create_movement_no_commit(
        self,
        process_id: int,
        title: str,
        occurred_at: datetime,
        source: MovementSource,
        description: str | None = None,
        created_by: int | None = None,
    ) -> ProcessMovement:
        movement = ProcessMovement(
            process_id=process_id,
            title=title,
            description=description,
            occurred_at=occurred_at,
            source=source,
            created_by=created_by,
        )
        self.db.add(movement)
        self.db.flush()
        return movement

    def create_movement(
        self,
        process_id: int,
        title: str,
        occurred_at: datetime,
        source: MovementSource,
        description: str | None = None,
        created_by: int | None = None,
    ) -> ProcessMovement:
        movement = self.create_movement_no_commit(
            process_id=process_id,
            title=title,
            occurred_at=occurred_at,
            source=source,
            description=description,
            created_by=created_by,
        )
        self.db.commit()
        return self.db.scalars(
            self._movement_query().where(ProcessMovement.id == movement.id)
        ).first()

    def reload_movement(self, movement_id: int) -> ProcessMovement | None:
        return self.db.scalars(
            self._movement_query().where(ProcessMovement.id == movement_id)
        ).first()

    def list_movements(
        self,
        process_id: int,
        source: MovementSource | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ProcessMovement], int]:
        base = select(ProcessMovement).where(ProcessMovement.process_id == process_id)

        if source is not None:
            base = base.where(ProcessMovement.source == source)
        if date_from is not None:
            base = base.where(ProcessMovement.occurred_at >= date_from)
        if date_to is not None:
            base = base.where(ProcessMovement.occurred_at <= date_to)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.options(joinedload(ProcessMovement.creator))
                .order_by(ProcessMovement.occurred_at.desc(), ProcessMovement.id.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
            .unique()
            .all()
        )
        return items, total

    def _note_query(self):
        return select(ProcessNote).options(
            joinedload(ProcessNote.creator),
            joinedload(ProcessNote.updater),
        )

    def create_note(self, process_id: int, created_by: int, content: str) -> ProcessNote:
        note = ProcessNote(
            process_id=process_id, created_by=created_by, content=content
        )
        self.db.add(note)
        self.db.commit()
        return self.db.scalars(
            self._note_query().where(ProcessNote.id == note.id)
        ).first()

    def get_note_by_id(self, note_id: int, process_id: int) -> ProcessNote | None:
        return self.db.scalars(
            self._note_query().where(
                ProcessNote.id == note_id,
                ProcessNote.process_id == process_id,
            )
        ).first()

    def list_notes_by_process(
        self, process_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[ProcessNote], int]:
        base = select(ProcessNote).where(ProcessNote.process_id == process_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        notes = list(
            self.db.scalars(
                self._note_query()
                .where(ProcessNote.process_id == process_id)
                .order_by(ProcessNote.created_at.desc(), ProcessNote.id.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
            .unique()
            .all()
        )
        return notes, total

    def update_note(
        self, note: ProcessNote, content: str, updated_by: int
    ) -> ProcessNote:
        note.content = content
        note.updated_by = updated_by
        self.db.commit()
        return self.db.scalars(
            self._note_query().where(ProcessNote.id == note.id)
        ).first()
