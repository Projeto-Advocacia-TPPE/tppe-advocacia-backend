from app.modules.clients.model import Client, ClientNote
from app.modules.clients.repository import ClientRepository
from app.modules.clients.schema import (
    ClientCreate,
    ClientNoteCreate,
    ClientNoteUpdate,
    ClientUpdate,
)
from app.modules.users.model import Role, User
from app.shared.exceptions import (
    ClientCnpjAlreadyExistsError,
    ClientCpfAlreadyExistsError,
    ClientNoteNotFoundError,
    ClientNotFoundError,
    ForbiddenError,
)


class ClientService:
    def __init__(self, repository: ClientRepository) -> None:
        self.repository = repository

    def create_client(self, payload: ClientCreate, created_by: User) -> Client:
        if payload.cpf and self.repository.get_by_cpf(payload.cpf):
            raise ClientCpfAlreadyExistsError()

        if payload.cnpj and self.repository.get_by_cnpj(payload.cnpj):
            raise ClientCnpjAlreadyExistsError()

        return self.repository.create(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            cpf=payload.cpf,
            cnpj=payload.cnpj,
            address=payload.address,
            created_by=created_by.id,
        )

    def get_client(self, client_id: int) -> Client:
        client = self.repository.get_by_id(client_id)

        if client is None:
            raise ClientNotFoundError()

        return client

    def list_clients(
        self,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Client], int]:
        return self.repository.list(search=search, page=page, limit=limit)

    def update_client(
        self, client_id: int, payload: ClientUpdate, updated_by: User
    ) -> Client:
        client = self.get_client(client_id)
        data = payload.model_dump(exclude_none=True)

        if not data:
            return client

        if "cpf" in data and data["cpf"] != client.cpf:
            existing = self.repository.get_by_cpf(data["cpf"])
            if existing and existing.id != client_id:
                raise ClientCpfAlreadyExistsError()
            data["cnpj"] = None
        elif "cnpj" in data and data["cnpj"] != client.cnpj:
            existing = self.repository.get_by_cnpj(data["cnpj"])
            if existing and existing.id != client_id:
                raise ClientCnpjAlreadyExistsError()
            data["cpf"] = None

        data["updated_by"] = updated_by.id
        return self.repository.update(client, data)

    def create_note(
        self, client_id: int, payload: ClientNoteCreate, current_user: User
    ) -> ClientNote:
        self.get_client(client_id)
        return self.repository.create_note(
            client_id=client_id,
            created_by=current_user.id,
            content=payload.content,
        )

    def list_notes(
        self, client_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[ClientNote], int]:
        self.get_client(client_id)
        return self.repository.list_notes_by_client(
            client_id=client_id, page=page, limit=limit
        )

    def update_note(
        self,
        client_id: int,
        note_id: int,
        payload: ClientNoteUpdate,
        current_user: User,
    ) -> ClientNote:
        self.get_client(client_id)
        note = self.repository.get_note_by_id(note_id=note_id, client_id=client_id)

        if note is None:
            raise ClientNoteNotFoundError()

        if note.created_by != current_user.id and current_user.role != Role.ADMIN:
            raise ForbiddenError()

        return self.repository.update_note(
            note=note, content=payload.content, updated_by=current_user.id
        )
