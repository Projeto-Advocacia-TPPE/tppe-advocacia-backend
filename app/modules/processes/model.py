from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.clients.model import Client
from app.shared.base_model import Base


class ProcessStatus(str, Enum):
    ATIVO = "ATIVO"
    SUSPENSO = "SUSPENSO"
    ARQUIVADO = "ARQUIVADO"
    ENCERRADO = "ENCERRADO"


class Process(Base):
    __tablename__ = "processes"
    __table_args__ = (UniqueConstraint("number", name="uq_processes_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    court: Mapped[str] = mapped_column(String(120), nullable=False)
    action_type: Mapped[str] = mapped_column(String(120), nullable=False)
    opposing_party: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ProcessStatus] = mapped_column(
        SAEnum(ProcessStatus, native_enum=False, length=20),
        nullable=False,
        default=ProcessStatus.ATIVO,
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_processes_created_by"),
        nullable=True,
    )
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_processes_updated_by"),
        nullable=True,
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

    client: Mapped[Client | None] = relationship("Client", foreign_keys=[client_id])
