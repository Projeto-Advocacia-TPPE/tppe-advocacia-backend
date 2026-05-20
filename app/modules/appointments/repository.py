from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.modules.appointments.model import Appointment, AppointmentType


class AppointmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _query(self):
        return select(Appointment).options(joinedload(Appointment.creator))

    def get_by_id(self, appointment_id: int) -> Appointment | None:
        return self.db.scalars(
            self._query().where(Appointment.id == appointment_id)
        ).first()

    def create(
        self,
        title: str,
        type: AppointmentType,
        starts_at: datetime,
        duration_minutes: int,
        description: str | None,
        location: str | None,
        client_id: int | None,
        process_id: int | None,
        created_by: int,
    ) -> Appointment:
        appointment = Appointment(
            title=title,
            type=type,
            starts_at=starts_at,
            duration_minutes=duration_minutes,
            description=description,
            location=location,
            client_id=client_id,
            process_id=process_id,
            created_by=created_by,
        )
        self.db.add(appointment)
        self.db.commit()
        return self.get_by_id(appointment.id)

    def update(self, appointment: Appointment, data: dict) -> Appointment:
        for key, value in data.items():
            setattr(appointment, key, value)
        self.db.commit()
        return self.get_by_id(appointment.id)

    def delete(self, appointment: Appointment) -> None:
        self.db.delete(appointment)
        self.db.commit()

    def list(
        self,
        created_by: int,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        type: AppointmentType | None = None,
        client_id: int | None = None,
        process_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Appointment], int]:
        base = select(Appointment).where(Appointment.created_by == created_by)

        if date_from is not None:
            base = base.where(Appointment.starts_at >= date_from)
        if date_to is not None:
            base = base.where(Appointment.starts_at <= date_to)
        if type is not None:
            base = base.where(Appointment.type == type)
        if client_id is not None:
            base = base.where(Appointment.client_id == client_id)
        if process_id is not None:
            base = base.where(Appointment.process_id == process_id)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.options(joinedload(Appointment.creator))
                .order_by(Appointment.starts_at.asc(), Appointment.id.asc())
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()
        )
        return items, total
