from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.leads.model import Lead
from app.modules.leads.schema import LeadCreate


class LeadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[Lead]:
        statement = select(Lead).order_by(Lead.created_at.desc())
        return list(self.db.scalars(statement).all())

    def create(self, payload: LeadCreate) -> Lead:
        lead = Lead(**payload.model_dump(), status="novo")
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead
