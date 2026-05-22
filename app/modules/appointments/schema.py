from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.appointments.model import AppointmentType


class AppointmentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    type: AppointmentType
    starts_at: datetime
    duration_minutes: int = Field(..., gt=0, le=1440)
    client_id: int | None = None
    process_id: int | None = None
    description: str | None = Field(None, max_length=5000)
    location: str | None = Field(None, max_length=255)

    @field_validator("starts_at")
    @classmethod
    def starts_at_not_in_past(cls, value: datetime) -> datetime:
        compare = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if compare < datetime.now(timezone.utc):
            raise ValueError("starts_at cannot be in the past")
        return value


class AppointmentUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=150)
    type: AppointmentType | None = None
    starts_at: datetime | None = None
    duration_minutes: int | None = Field(None, gt=0, le=1440)
    client_id: int | None = None
    process_id: int | None = None
    description: str | None = Field(None, max_length=5000)
    location: str | None = Field(None, max_length=255)

    model_config = ConfigDict(extra="forbid")


class AppointmentSyncResult(BaseModel):
    total: int
    synced: int
    failed: int


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    type: AppointmentType
    starts_at: datetime
    duration_minutes: int
    description: str | None
    location: str | None
    client_id: int | None
    process_id: int | None
    created_by: int
    created_by_name: str
    google_event_id: str | None
    is_synced_to_google: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def resolve_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "title": data.title,
            "type": data.type,
            "starts_at": data.starts_at,
            "duration_minutes": data.duration_minutes,
            "description": data.description,
            "location": data.location,
            "client_id": data.client_id,
            "process_id": data.process_id,
            "created_by": data.created_by,
            "created_by_name": data.creator.name if data.creator else "",
            "google_event_id": data.google_event_id,
            "is_synced_to_google": data.is_synced_to_google,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
        }
