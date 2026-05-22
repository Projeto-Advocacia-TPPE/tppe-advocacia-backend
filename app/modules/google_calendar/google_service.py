from __future__ import annotations

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config.settings import Settings
from app.modules.google_calendar.oauth import SCOPES

_TOKEN_URI = "https://oauth2.googleapis.com/token"  # public OAuth URL  # nosec B105
_CALENDAR_ID = "primary"


class GoogleCalendarApiClient:
    """Implementação real de `GoogleCalendarClient` via Google Calendar API.

    A cada chamada constrói credenciais a partir do refresh_token — a lib
    do Google obtém um access_token novo automaticamente.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _service(self, refresh_token: str):
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=_TOKEN_URI,
            client_id=self._settings.google_client_id,
            client_secret=self._settings.google_client_secret,
            scopes=SCOPES,
        )
        return build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def create_event(self, refresh_token: str, event: dict) -> str:
        created = (
            self._service(refresh_token)
            .events()
            .insert(calendarId=_CALENDAR_ID, body=event)
            .execute()
        )
        return created["id"]

    def update_event(self, refresh_token: str, event_id: str, event: dict) -> None:
        self._service(refresh_token).events().update(
            calendarId=_CALENDAR_ID, eventId=event_id, body=event
        ).execute()

    def delete_event(self, refresh_token: str, event_id: str) -> None:
        self._service(refresh_token).events().delete(
            calendarId=_CALENDAR_ID, eventId=event_id
        ).execute()
