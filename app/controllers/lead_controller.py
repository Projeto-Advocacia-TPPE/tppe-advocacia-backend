from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.schemas.lead import LeadCreate


def list_leads(db: Session) -> list[Lead]:
    statement = select(Lead).order_by(Lead.created_at.desc())
    return list(db.scalars(statement).all())


def create_lead(db: Session, payload: LeadCreate) -> Lead:
    lead = Lead(**payload.model_dump(), status="novo")
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

