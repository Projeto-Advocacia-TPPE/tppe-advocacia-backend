from app.modules.clients.model import Client
from app.modules.clients.repository import ClientRepository
from app.modules.clients.schema import ClientCreate, ClientUpdate
from app.modules.users.model import User
from app.shared.exceptions import (
    ClientCnpjAlreadyExistsError,
    ClientCpfAlreadyExistsError,
    ClientNotFoundError,
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
