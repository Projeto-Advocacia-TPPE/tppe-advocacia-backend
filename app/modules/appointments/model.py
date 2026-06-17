from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.clients.model import Client
from app.modules.processes.model import Process
from app.modules.users.model import User
from app.shared.db.base_model import Base


class AppointmentType(str, Enum):
    AUDIENCIA = "AUDIENCIA"
    REUNIAO = "REUNIAO"
    PRAZO = "PRAZO"
    OUTRO = "OUTRO"


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_created_by", "created_by"),
        Index("ix_appointments_starts_at", "starts_at"),
        Index("ix_appointments_client_id", "client_id"),
        Index("ix_appointments_process_id", "process_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[AppointmentType] = mapped_column(
        SAEnum(AppointmentType, native_enum=False, length=20),
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=True,
    )
    process_id: Mapped[int | None] = mapped_column(
        ForeignKey("processes.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_appointments_created_by"),
        nullable=False,
    )
    # Campos da integração Google Calendar
    google_event_id: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_synced_to_google: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    creator: Mapped[User] = relationship("User", foreign_keys=[created_by])
    client: Mapped[Client | None] = relationship("Client", foreign_keys=[client_id])
    process: Mapped[Process | None] = relationship("Process", foreign_keys=[process_id])
