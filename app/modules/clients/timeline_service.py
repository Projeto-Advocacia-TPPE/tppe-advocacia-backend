from __future__ import annotations

from app.modules.clients.repository import ClientRepository
from app.modules.clients.schema import (
    ClientNoteRead,
    ClientRead,
    ClientTimelineRead,
    MovementSummary,
    ProcessSummary,
    RecentActivityItem,
)
from app.modules.clients.timeline_repository import TimelineRepository
from app.modules.processes.repository import ProcessRepository
from app.shared.exceptions import ClientNotFoundError


class ClientTimelineService:
    def __init__(
        self,
        client_repository: ClientRepository,
        process_repository: ProcessRepository,
        timeline_repository: TimelineRepository,
    ) -> None:
        self.client_repository = client_repository
        self.process_repository = process_repository
        self.timeline_repository = timeline_repository

    def get_timeline(
        self,
        client_id: int,
        notes_limit: int = 10,
        processes_limit: int = 20,
        activity_limit: int = 20,
    ) -> ClientTimelineRead:
        client = self.client_repository.get_by_id(client_id)
        if client is None:
            raise ClientNotFoundError()

        notes = self.client_repository.list_recent_notes(
            client_id=client_id, limit=notes_limit
        )
        processes_with_lm = self.process_repository.get_processes_with_last_movement(
            client_id=client_id, limit=processes_limit
        )
        activity_rows = self.timeline_repository.get_recent_activity(
            client_id=client_id, limit=activity_limit
        )

        processes = [
            ProcessSummary(
                id=process.id,
                number=process.number,
                action_type=process.action_type,
                court=process.court,
                status=process.status,
                created_at=process.created_at,
                last_movement=(
                    MovementSummary(
                        id=last.id,
                        title=last.title,
                        occurred_at=last.occurred_at,
                        source=last.source,
                    )
                    if last is not None
                    else None
                ),
            )
            for process, last in processes_with_lm
        ]

        return ClientTimelineRead(
            client=ClientRead.model_validate(client),
            notes=[ClientNoteRead.model_validate(n) for n in notes],
            processes=processes,
            recent_activity=[RecentActivityItem(**row) for row in activity_rows],
        )
