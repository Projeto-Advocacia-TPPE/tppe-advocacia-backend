from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.leads.model import Lead, LeadStatus


class LeadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(
        self,
        status: LeadStatus | None = None,
        assigned_to: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Lead], int]:
        base = select(Lead)

        if status is not None:
            base = base.where(Lead.status == status)

        if assigned_to is not None:
            base = base.where(Lead.assigned_to == assigned_to)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        leads = list(
            self.db.scalars(
                base.order_by(Lead.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()
        )
        return leads, total

    def get_by_id(self, lead_id: int) -> Lead | None:
        return self.db.scalars(select(Lead).where(Lead.id == lead_id)).first()

    def find_recent_by_email(self, email: str, window_hours: int) -> Lead | None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        return self.db.scalars(
            select(Lead).where(Lead.email == email).where(Lead.created_at >= cutoff)
        ).first()

    def create(
        self,
        name: str,
        email: str,
        phone: str | None = None,
        message: str | None = None,
    ) -> Lead:
        lead = Lead(
            name=name, email=email, phone=phone, message=message, status=LeadStatus.NOVO
        )
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def update(self, lead: Lead, data: dict) -> Lead:
        for key, value in data.items():
            setattr(lead, key, value)
        self.db.commit()
        self.db.refresh(lead)
        return lead
