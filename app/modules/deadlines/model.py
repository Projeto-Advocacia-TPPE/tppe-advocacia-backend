from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class Deadline(Base):
    __tablename__ = "deadlines"
    __table_args__ = (Index("ix_deadlines_process_due", "process_id", "due_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    process_id: Mapped[int] = mapped_column(
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    business_days: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline_type: Mapped[str] = mapped_column(String(120), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    court: Mapped[str | None] = mapped_column(String(120), nullable=True)
    comarca: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_deadlines_created_by"),
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
