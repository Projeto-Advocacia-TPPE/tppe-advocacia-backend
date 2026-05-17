import re
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.processes.model import MovementSource, ProcessStatus

CNJ_MASKED_REGEX = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")
CNJ_DIGITS_REGEX = re.compile(r"^\d{20}$")


def normalize_cnj(raw: str) -> str:
    if not isinstance(raw, str):
        raise ValueError("Número CNJ deve ser string")

    digits_only = re.sub(r"\D", "", raw.strip())
    if CNJ_DIGITS_REGEX.match(digits_only):
        return digits_only

    raise ValueError("Número CNJ inválido")


def format_cnj(digits: str) -> str:
    if not CNJ_DIGITS_REGEX.match(digits):
        return digits
    return (
        f"{digits[0:7]}-{digits[7:9]}.{digits[9:13]}."
        f"{digits[13:14]}.{digits[14:16]}.{digits[16:20]}"
    )


class ProcessCreate(BaseModel):
    number: str = Field(..., min_length=1, max_length=25)
    client_id: int | None = Field(default=None, gt=0)
    court: str = Field(..., min_length=1, max_length=120)
    action_type: str = Field(..., min_length=1, max_length=120)
    opposing_party: str | None = Field(default=None, max_length=255)

    @field_validator("number")
    @classmethod
    def validate_number(cls, value: str) -> str:
        return normalize_cnj(value)


class ProcessRead(BaseModel):
    id: int
    number: str
    client_id: int | None
    client_name: str | None
    court: str
    action_type: str
    opposing_party: str | None
    status: ProcessStatus
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "number": format_cnj(data.number),
            "client_id": data.client_id,
            "client_name": data.client.name if data.client else None,
            "court": data.court,
            "action_type": data.action_type,
            "opposing_party": data.opposing_party,
            "status": data.status,
            "created_by": data.created_by,
            "updated_by": data.updated_by,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
        }


class ProcessStatusChange(BaseModel):
    status: ProcessStatus
    reason: str | None = Field(default=None, max_length=500)


class ProcessStatusChangeResponse(BaseModel):
    id: int
    number: str
    client_id: int | None
    client_name: str | None
    court: str
    action_type: str
    opposing_party: str | None
    status: ProcessStatus
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime
    last_status_change_movement_id: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_process(
        cls, process: object, movement_id: int
    ) -> "ProcessStatusChangeResponse":
        return cls(
            id=process.id,
            number=format_cnj(process.number),
            client_id=process.client_id,
            client_name=process.client.name if process.client else None,
            court=process.court,
            action_type=process.action_type,
            opposing_party=process.opposing_party,
            status=process.status,
            created_by=process.created_by,
            updated_by=process.updated_by,
            created_at=process.created_at,
            updated_at=process.updated_at,
            last_status_change_movement_id=movement_id,
        )


class ProcessListItem(BaseModel):
    id: int
    number: str
    client_id: int | None
    client_name: str | None
    court: str
    action_type: str
    status: ProcessStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "number": format_cnj(data.number),
            "client_id": data.client_id,
            "client_name": data.client.name if data.client else None,
            "court": data.court,
            "action_type": data.action_type,
            "status": data.status,
            "created_at": data.created_at,
        }


class MovementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    occurred_at: datetime | None = Field(default=None)

    @field_validator("occurred_at")
    @classmethod
    def validate_not_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        reference = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if reference > datetime.now(timezone.utc):
            raise ValueError("occurred_at não pode estar no futuro")
        return value


class MovementRead(BaseModel):
    id: int
    process_id: int
    title: str
    description: str | None
    occurred_at: datetime
    source: MovementSource
    created_by: int | None
    created_by_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_creator_name(cls, data: object) -> object:
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "process_id": data.process_id,
            "title": data.title,
            "description": data.description,
            "occurred_at": data.occurred_at,
            "source": data.source,
            "created_by": data.created_by,
            "created_by_name": data.creator.name if data.creator else None,
            "created_at": data.created_at,
        }
