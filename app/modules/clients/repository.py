from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.clients.model import Client, ClientNote


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

    def get_by_id(self, client_id: int) -> Client | None:
        return self.db.scalars(select(Client).where(Client.id == client_id)).first()

    def get_by_cpf(self, cpf: str) -> Client | None:
        return self.db.scalars(select(Client).where(Client.cpf == cpf)).first()

    def get_by_cnpj(self, cnpj: str) -> Client | None:
        return self.db.scalars(select(Client).where(Client.cnpj == cnpj)).first()

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

    def _note_query(self) -> object:
        return select(ClientNote).options(
            joinedload(ClientNote.creator),
            joinedload(ClientNote.updater),
        )

    def create_note(self, client_id: int, created_by: int, content: str) -> ClientNote:
        note = ClientNote(client_id=client_id, created_by=created_by, content=content)
        self.db.add(note)
        self.db.commit()
        return self.db.scalars(
            self._note_query().where(ClientNote.id == note.id)
        ).first()

    def get_note_by_id(self, note_id: int, client_id: int) -> ClientNote | None:
        return self.db.scalars(
            self._note_query().where(
                ClientNote.id == note_id,
                ClientNote.client_id == client_id,
            )
        ).first()

    def list_notes_by_client(
        self, client_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[ClientNote], int]:
        base = select(ClientNote).where(ClientNote.client_id == client_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        notes = list(
            self.db.scalars(
                self._note_query()
                .where(ClientNote.client_id == client_id)
                .order_by(ClientNote.created_at.desc(), ClientNote.id.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
            .unique()
            .all()
        )
        return notes, total

    def list_recent_notes(self, client_id: int, limit: int) -> list[ClientNote]:
        return list(
            self.db.scalars(
                self._note_query()
                .where(ClientNote.client_id == client_id)
                .order_by(ClientNote.created_at.desc(), ClientNote.id.desc())
                .limit(limit)
            )
            .unique()
            .all()
        )

    def update_note(
        self, note: ClientNote, content: str, updated_by: int
    ) -> ClientNote:
        note.content = content
        note.updated_by = updated_by
        self.db.commit()
        return self.db.scalars(
            self._note_query().where(ClientNote.id == note.id)
        ).first()
