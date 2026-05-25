from functools import lru_cache

from app.config.settings import get_settings
from app.modules.google_calendar.google_service import GoogleCalendarApiClient


@lru_cache(maxsize=1)
def get_google_calendar_client() -> GoogleCalendarApiClient:
    return GoogleCalendarApiClient(get_settings())
