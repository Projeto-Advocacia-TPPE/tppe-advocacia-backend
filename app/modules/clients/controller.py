from sqlalchemy.orm import Session

from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.clients.schema import ClientCreate, ClientUpdate
from app.modules.clients.service import ClientService
from app.modules.users.model import User


class ClientController:
    def __init__(self, db: Session) -> None:
        self.service = ClientService(ClientRepository(db))

    def create_client(self, payload: ClientCreate, created_by: User) -> Client:
        return self.service.create_client(payload, created_by=created_by)

    def get_client(self, client_id: int) -> Client:
        return self.service.get_client(client_id)

    def list_clients(
        self,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Client], int]:
        return self.service.list_clients(search=search, page=page, limit=limit)

    def update_client(
        self, client_id: int, payload: ClientUpdate, updated_by: User
    ) -> Client:
        return self.service.update_client(client_id, payload, updated_by=updated_by)
