from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.modules.users.model import Role


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: Role | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
