from __future__ import annotations

from app.modules.appointments.model import Appointment
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schema import AppointmentCreate, AppointmentUpdate
from app.modules.clients.repository import ClientRepository
from app.modules.processes.repository import ProcessRepository
from app.modules.users.model import User
from app.shared.exceptions import (
    AppointmentClientNotFoundError,
    AppointmentNotFoundError,
    AppointmentProcessNotFoundError,
    ForbiddenError,
)
from app.shared.types import Role


class AppointmentService:
    def __init__(
        self,
        repository: AppointmentRepository,
        clients: ClientRepository,
        processes: ProcessRepository,
    ) -> None:
        self.repository = repository
        self.clients = clients
        self.processes = processes

    def create_appointment(
        self, payload: AppointmentCreate, created_by: User
    ) -> Appointment:
        self._validate_references(payload.client_id, payload.process_id)
        return self.repository.create(
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

        return self.repository.update(appointment, data)

    def delete_appointment(self, appointment_id: int, current_user: User) -> None:
        appointment = self._get_or_404(appointment_id)
        self._authorize(appointment, current_user)
        self.repository.delete(appointment)

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
