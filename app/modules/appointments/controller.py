from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schema import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentSyncResult,
    AppointmentUpdate,
)
from app.modules.appointments.service import AppointmentService
from app.modules.clients.repository import ClientRepository
from app.modules.google_calendar.protocol import GoogleCalendarClient
from app.modules.google_calendar.service import build_google_calendar_service
from app.modules.processes.repository import ProcessRepository
from app.modules.users.model import User


class AppointmentController:
    def __init__(self, db: Session, google_client: GoogleCalendarClient) -> None:
        self.service = AppointmentService(
            AppointmentRepository(db),
            ClientRepository(db),
            ProcessRepository(db),
            google_sync=build_google_calendar_service(db, google_client),
        )

    def create_appointment(
        self, payload: AppointmentCreate, created_by: User
    ) -> AppointmentRead:
        appointment = self.service.create_appointment(payload, created_by)
        return AppointmentRead.model_validate(appointment)

    def list_appointments(
        self, current_user: User, **filters
    ) -> tuple[list[AppointmentRead], int]:
        items, total = self.service.list_appointments(current_user, **filters)
        return [AppointmentRead.model_validate(a) for a in items], total

    def get_appointment(
        self, appointment_id: int, current_user: User
    ) -> AppointmentRead:
        appointment = self.service.get_appointment(appointment_id, current_user)
        return AppointmentRead.model_validate(appointment)

    def update_appointment(
        self, appointment_id: int, payload: AppointmentUpdate, current_user: User
    ) -> AppointmentRead:
        appointment = self.service.update_appointment(
            appointment_id, payload, current_user
        )
        return AppointmentRead.model_validate(appointment)

    def delete_appointment(self, appointment_id: int, current_user: User) -> None:
        self.service.delete_appointment(appointment_id, current_user)

    def sync_all_to_google(self, current_user: User) -> AppointmentSyncResult:
        return self.service.sync_all_to_google(current_user)
