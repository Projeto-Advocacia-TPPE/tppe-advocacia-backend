from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.clients.model import Client


class ClientRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        cpf: str | None = None,
        cnpj: str | None = None,
        address: str | None = None,
        created_by: int | None = None,
    ) -> Client:
        client = Client(
            name=name,
            email=email,
            phone=phone,
            cpf=cpf,
            cnpj=cnpj,
            address=address,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def list(
        self,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Client], int]:
        base = select(Client)

        if search:
            base = base.where(
                or_(
                    func.lower(Client.name).contains(search.lower()),
                    Client.cpf == search,
                    Client.cnpj == search,
                )
            )

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        clients = list(
            self.db.scalars(
                base.order_by(Client.name.asc()).offset((page - 1) * limit).limit(limit)
            ).all()
        )
        return clients, total

    def update(self, client: Client, data: dict) -> Client:
        for key, value in data.items():
            setattr(client, key, value)
        self.db.commit()
        self.db.refresh(client)
        return client
