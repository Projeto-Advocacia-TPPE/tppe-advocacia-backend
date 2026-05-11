import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class AuditAction(enum.Enum):
    USER_CREATED = "USER_CREATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)
    performed_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    performed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    target_user_role: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
