from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SkipReason(str, Enum):
    WEEKEND = "WEEKEND"
    HOLIDAY = "HOLIDAY"


class SkippedDay(BaseModel):
    date: date
    reason: SkipReason
    description: str | None = None


class DeadlineCalculateRequest(BaseModel):
    start_date: date
    business_days: int = Field(gt=0, le=3650)
    court: str | None = Field(default=None, max_length=120)
    comarca: str | None = Field(default=None, max_length=120)


class DeadlineCalculateResponse(BaseModel):
    start_date: date
    business_days: int
    due_date: date
    court: str | None
    comarca: str | None
    skipped_days: list[SkippedDay]


class DeadlineCreate(BaseModel):
    start_date: date
    business_days: int = Field(gt=0, le=3650)
    deadline_type: str = Field(min_length=1, max_length=120)
    comarca: str | None = Field(default=None, max_length=120)


class DeadlineUpdate(BaseModel):
    start_date: date | None = None
    business_days: int | None = Field(default=None, gt=0, le=3650)
    deadline_type: str | None = Field(default=None, min_length=1, max_length=120)
    comarca: str | None = Field(default=None, max_length=120)


class DeadlineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_id: int
    start_date: date
    business_days: int
    deadline_type: str
    due_date: date
    court: str | None
    comarca: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class DeadlineAlertKind(str, Enum):
    APPROACHING = "APPROACHING"
    EXPIRED = "EXPIRED"


class DeadlineAlertRead(BaseModel):
    id: int
    deadline_id: int
    days_before: int
    kind: DeadlineAlertKind
    sent_at: datetime
