from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.leads.model import LeadStatus


class LeadBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    message: str | None = Field(default=None, max_length=1000)


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    assigned_to: int | None = None


class LeadRead(LeadBase):
    id: int
    status: LeadStatus
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
