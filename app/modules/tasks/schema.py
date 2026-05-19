from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.tasks.model import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(None, max_length=5000)
    due_date: datetime | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: int | None = None
    client_id: int | None = None
    process_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = Field(None, max_length=5000)
    due_date: datetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assigned_to: int | None = None
    client_id: int | None = None
    process_id: int | None = None

    model_config = ConfigDict(extra="forbid")


class TaskMove(BaseModel):
    status: TaskStatus
    order: int = Field(..., ge=0)


class TaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    due_date: datetime | None
    priority: TaskPriority
    status: TaskStatus
    order: int
    assigned_to: int | None
    assigned_to_name: str | None
    client_id: int | None
    process_id: int | None
    created_by: int
    created_by_name: str
    updated_by: int | None
    completed_at: datetime | None
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
            "title": data.title,
            "description": data.description,
            "due_date": data.due_date,
            "priority": data.priority,
            "status": data.status,
            "order": data.order,
            "assigned_to": data.assigned_to,
            "assigned_to_name": data.assignee.name if data.assignee else None,
            "client_id": data.client_id,
            "process_id": data.process_id,
            "created_by": data.created_by,
            "created_by_name": data.creator.name if data.creator else "",
            "updated_by": data.updated_by,
            "completed_at": data.completed_at,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
        }
