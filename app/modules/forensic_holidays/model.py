from datetime import date as _date
from datetime import datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Index, String, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class HolidayScope(str, Enum):
    NATIONAL = "NATIONAL"
    COURT = "COURT"
    COMARCA = "COMARCA"


class ForensicHoliday(Base):
    __tablename__ = "forensic_holidays"
    __table_args__ = (
        Index("ix_forensic_holidays_date", "date"),
        Index(
            "ix_forensic_holidays_scope_court_comarca",
            "scope",
            "court",
            "comarca",
        ),
        UniqueConstraint(
            "date",
            "scope",
            "court",
            "comarca",
            name="uq_forensic_holidays_natural",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[_date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[HolidayScope] = mapped_column(
        SAEnum(HolidayScope, native_enum=False, length=20),
        nullable=False,
    )
    court: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comarca: Mapped[str | None] = mapped_column(String(120), nullable=True)
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
