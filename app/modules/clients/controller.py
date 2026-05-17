from sqlalchemy.orm import Session

from app.modules.clients.model import Client, ClientNote
from app.modules.clients.repository import ClientRepository
from app.modules.clients.schema import (
    ClientCreate,
    ClientNoteCreate,
    ClientNoteUpdate,
    ClientUpdate,
)
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

    def create_note(
        self, client_id: int, payload: ClientNoteCreate, current_user: User
    ) -> ClientNote:
        return self.service.create_note(client_id, payload, current_user=current_user)

    def list_notes(
        self, client_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[ClientNote], int]:
        return self.service.list_notes(client_id, page=page, limit=limit)

    def update_note(
        self,
        client_id: int,
        note_id: int,
        payload: ClientNoteUpdate,
        current_user: User,
    ) -> ClientNote:
        return self.service.update_note(
            client_id, note_id, payload, current_user=current_user
        )
