from datetime import datetime

from pydantic import BaseModel


class GoogleAuthUrlRead(BaseModel):
    auth_url: str


class GoogleStatusRead(BaseModel):
    connected: bool
    connected_at: datetime | None = None
    scope: str | None = None
