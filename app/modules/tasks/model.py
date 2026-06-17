from datetime import datetime
from enum import Enum

from sqlalchemy import (
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


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_status_order", "status", "order"),
        Index("ix_tasks_assigned_to", "assigned_to"),
        Index("ix_tasks_client_id", "client_id"),
        Index("ix_tasks_process_id", "process_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority, native_enum=False, length=10),
        nullable=False,
        default=TaskPriority.MEDIUM,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, native_enum=False, length=20),
        nullable=False,
        default=TaskStatus.TODO,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_tasks_assigned_to"),
        nullable=True,
    )
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=True,
    )
    process_id: Mapped[int | None] = mapped_column(
        ForeignKey("processes.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_tasks_created_by"),
        nullable=False,
    )
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_tasks_updated_by"),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    assignee: Mapped[User | None] = relationship("User", foreign_keys=[assigned_to])
    creator: Mapped[User] = relationship("User", foreign_keys=[created_by])
    client: Mapped[Client | None] = relationship("Client", foreign_keys=[client_id])
    process: Mapped[Process | None] = relationship("Process", foreign_keys=[process_id])
