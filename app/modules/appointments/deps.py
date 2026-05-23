from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.service import AppointmentService
from app.modules.clients.repository import ClientRepository
from app.modules.google_calendar.google_service import GoogleCalendarApiClient
from app.modules.google_calendar.service import build_google_calendar_service
from app.modules.processes.repository import ProcessRepository
from app.shared.google_deps import get_google_calendar_client


def get_appointment_service(
    db: Session = Depends(get_db),
    google_client: GoogleCalendarApiClient = Depends(get_google_calendar_client),
) -> AppointmentService:
    return AppointmentService(
        AppointmentRepository(db),
        ClientRepository(db),
        ProcessRepository(db),
        google_sync=build_google_calendar_service(db, google_client),
    )
