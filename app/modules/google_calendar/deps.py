from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.google_calendar.google_service import GoogleCalendarApiClient
from app.modules.google_calendar.service import GoogleCalendarService, build_google_calendar_service
from app.shared.google_deps import get_google_calendar_client


def get_google_calendar_service(
    db: Session = Depends(get_db),
    client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
) -> GoogleCalendarService:
    return build_google_calendar_service(db, client)
