from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.modules.processes.model import MovementSource, ProcessStatus


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, pattern=r"^\d{11}$")
    cnpj: str | None = Field(default=None, pattern=r"^\d{14}$")
    address: str | None = None

    @model_validator(mode="after")
    def validate_cpf_cnpj(self) -> "ClientCreate":
        has_cpf = self.cpf is not None
        has_cnpj = self.cnpj is not None
        if has_cpf and has_cnpj:
            raise ValueError("CPF e CNPJ não podem ser informados simultaneamente")
        if not has_cpf and not has_cnpj:
            raise ValueError("Informe CPF ou CNPJ")
        return self


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, pattern=r"^\d{11}$")
    cnpj: str | None = Field(default=None, pattern=r"^\d{14}$")
    address: str | None = None

    @model_validator(mode="after")
    def validate_cpf_cnpj(self) -> "ClientUpdate":
        if self.cpf is not None and self.cnpj is not None:
            raise ValueError("CPF e CNPJ não podem ser informados simultaneamente")
        return self


class ClientRead(BaseModel):
    id: int
    name: str
    email: str | None
    phone: str | None
    cpf: str | None
    cnpj: str | None
    address: str | None
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientListItem(BaseModel):
    id: int
    name: str
    email: str | None
    phone: str | None
    cpf: str | None
    cnpj: str | None

    model_config = ConfigDict(from_attributes=True)


class ClientNoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class ClientNoteUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class ClientNoteRead(BaseModel):
    id: int
    client_id: int
    created_by: int
    updated_by: int | None
    created_by_name: str
    updated_by_name: str | None
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_author_names(cls, data: object) -> object:
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "client_id": data.client_id,
            "created_by": data.created_by,
            "updated_by": data.updated_by,
            "created_by_name": data.creator.name if data.creator else "",
            "updated_by_name": data.updater.name if data.updater else None,
            "content": data.content,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
        }


class MovementSummary(BaseModel):
    id: int
    title: str
    occurred_at: datetime
    source: MovementSource

    model_config = ConfigDict(from_attributes=True)


class ProcessSummary(BaseModel):
    id: int
    number: str
    action_type: str
    court: str
    status: ProcessStatus
    created_at: datetime
    last_movement: MovementSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class RecentActivityItem(BaseModel):
    kind: Literal["movement", "client_note"]
    process_id: int | None = None
    note_id: int | None = None
    title: str | None = None
    content: str | None = None
    occurred_at: datetime
    actor_id: int | None = None
    actor_name: str | None = None


class ClientTimelineRead(BaseModel):
    client: ClientRead
    notes: list[ClientNoteRead]
    processes: list[ProcessSummary]
    recent_activity: list[RecentActivityItem]
