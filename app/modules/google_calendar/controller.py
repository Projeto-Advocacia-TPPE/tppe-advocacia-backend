from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.google_calendar.protocol import GoogleCalendarClient
from app.modules.google_calendar.schema import GoogleAuthUrlRead, GoogleStatusRead
from app.modules.google_calendar.service import build_google_calendar_service


class GoogleCalendarController:
    def __init__(self, db: Session, client: GoogleCalendarClient) -> None:
        self.service = build_google_calendar_service(db, client)

    def get_auth_url(self, user_id: int) -> GoogleAuthUrlRead:
        return GoogleAuthUrlRead(auth_url=self.service.build_auth_url(user_id))

    def handle_callback(self, code: str, state: str) -> int:
        return self.service.handle_callback(code, state)

    def disconnect(self, user_id: int) -> None:
        self.service.disconnect(user_id)

    def get_status(self, user_id: int) -> GoogleStatusRead:
        return self.service.get_status(user_id)
