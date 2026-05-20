import enum

from pydantic import BaseModel, Field


class EventType(enum.Enum):
    PROCESS_MOVEMENT_CREATED = "PROCESS_MOVEMENT_CREATED"
    PROCESS_STATUS_CHANGED = "PROCESS_STATUS_CHANGED"
    LEAD_ASSIGNED = "LEAD_ASSIGNED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    DEADLINE_APPROACHING = "DEADLINE_APPROACHING"
    DEADLINE_EXPIRED = "DEADLINE_EXPIRED"
    EXTERNAL_API_FAILURE = "EXTERNAL_API_FAILURE"


class PreferencesRead(BaseModel):
    preferences: dict[EventType, bool]


class PreferencesUpdate(BaseModel):
    preferences: dict[EventType, bool] = Field(..., min_length=1)
