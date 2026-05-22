from app.config.settings import get_settings
from app.modules.google_calendar.google_service import GoogleCalendarApiClient


def get_google_calendar_client() -> GoogleCalendarApiClient:
    return GoogleCalendarApiClient(get_settings())
