import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.processes.model import ProcessStatus

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
