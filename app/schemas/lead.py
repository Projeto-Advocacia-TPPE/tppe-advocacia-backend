from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LeadBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    message: str | None = Field(default=None, max_length=1000)


class LeadCreate(LeadBase):
    pass


class LeadRead(LeadBase):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
