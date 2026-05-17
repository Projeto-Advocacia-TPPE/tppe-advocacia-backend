from sqlalchemy.orm import Session

from app.modules.clients.repository import ClientRepository
from app.modules.processes.model import Process, ProcessStatus
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.schema import ProcessCreate
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
