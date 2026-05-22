from __future__ import annotations

from datetime import datetime, timezone

from app.modules.appointments.model import Appointment
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schema import (
    AppointmentCreate,
    AppointmentSyncResult,
    AppointmentUpdate,
)
from app.modules.clients.repository import ClientRepository
from app.modules.google_calendar.service import (
    SYNC_CREATE,
    SYNC_DELETE,
    SYNC_UPDATE,
    GoogleCalendarService,
)
from app.modules.processes.repository import ProcessRepository
from app.modules.users.model import User
from app.shared.exceptions import (
    AppointmentClientNotFoundError,
    AppointmentNotFoundError,
    AppointmentProcessNotFoundError,
    ForbiddenError,
    GoogleNotConfiguredError,
    GoogleNotConnectedError,
)
from app.shared.types import Role


class AppointmentService:
    def __init__(
        self,
        repository: AppointmentRepository,
        clients: ClientRepository,
        processes: ProcessRepository,
        google_sync: GoogleCalendarService | None = None,
    ) -> None:
        self.repository = repository
        self.clients = clients
        self.processes = processes
        self.google_sync = google_sync

    def create_appointment(
        self, payload: AppointmentCreate, created_by: User
    ) -> Appointment:
        self._validate_references(payload.client_id, payload.process_id)
        appointment = self.repository.create(
            title=payload.title,
            type=payload.type,
            starts_at=payload.starts_at,
            duration_minutes=payload.duration_minutes,
            description=payload.description,
            location=payload.location,
            client_id=payload.client_id,
            process_id=payload.process_id,
            created_by=created_by.id,
        )
        return self._sync_google(appointment, SYNC_CREATE)

    def get_appointment(self, appointment_id: int, current_user: User) -> Appointment:
        appointment = self._get_or_404(appointment_id)
        self._authorize(appointment, current_user)
        return appointment

    def list_appointments(
        self, current_user: User, **filters
    ) -> tuple[list[Appointment], int]:
        return self.repository.list(created_by=current_user.id, **filters)

    def update_appointment(
        self, appointment_id: int, payload: AppointmentUpdate, current_user: User
    ) -> Appointment:
        appointment = self._get_or_404(appointment_id)
        self._authorize(appointment, current_user)

        data = payload.model_dump(exclude_unset=True)
        self._validate_references(data.get("client_id"), data.get("process_id"))

        appointment = self.repository.update(appointment, data)
        return self._sync_google(appointment, SYNC_UPDATE)

    def delete_appointment(self, appointment_id: int, current_user: User) -> None:
        appointment = self._get_or_404(appointment_id)
        self._authorize(appointment, current_user)
        if self.google_sync is not None:
            # Best-effort: apaga o evento no Google antes de remover local.
            self.google_sync.sync_appointment(appointment, SYNC_DELETE)
        self.repository.delete(appointment)

    def sync_all_to_google(self, current_user: User) -> AppointmentSyncResult:
        """Sincroniza retroativamente os compromissos futuros ainda não enviados.

        Idempotente: só varre os que têm `is_synced_to_google=False`, então
        rodar de novo não recria eventos já sincronizados.
        """
        if self.google_sync is None or not self.google_sync.is_configured:
            raise GoogleNotConfiguredError()
        if not self.google_sync.get_status(current_user.id).connected:
            raise GoogleNotConnectedError()

        appointments = self.repository.list_unsynced_future(
            current_user.id, datetime.now(timezone.utc)
        )
        synced = 0
        for appointment in appointments:
            event_id = self.google_sync.sync_appointment(appointment, SYNC_CREATE)
            if event_id is not None:
                self.repository.update(
                    appointment,
                    {"google_event_id": event_id, "is_synced_to_google": True},
                )
                synced += 1

        return AppointmentSyncResult(
            total=len(appointments),
            synced=synced,
            failed=len(appointments) - synced,
        )

    def _get_or_404(self, appointment_id: int) -> Appointment:
        appointment = self.repository.get_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError()
        return appointment

    @staticmethod
    def _authorize(appointment: Appointment, user: User) -> None:
        if user.role != Role.ADMIN and appointment.created_by != user.id:
            raise ForbiddenError()

    def _validate_references(
        self, client_id: int | None, process_id: int | None
    ) -> None:
        if client_id is not None and self.clients.get_by_id(client_id) is None:
            raise AppointmentClientNotFoundError()
        if process_id is not None and self.processes.get_by_id(process_id) is None:
            raise AppointmentProcessNotFoundError()

    def _sync_google(self, appointment: Appointment, action: str) -> Appointment:
        """Sincroniza com o Google e persiste o google_event_id resultante.

        Falha do Google é engolida dentro de `sync_appointment` — nunca
        bloqueia a operação local.
        """
        if self.google_sync is None:
            return appointment
        event_id = self.google_sync.sync_appointment(appointment, action)
        if event_id is not None and (
            event_id != appointment.google_event_id
            or not appointment.is_synced_to_google
        ):
            return self.repository.update(
                appointment,
                {"google_event_id": event_id, "is_synced_to_google": True},
            )
        return appointment
