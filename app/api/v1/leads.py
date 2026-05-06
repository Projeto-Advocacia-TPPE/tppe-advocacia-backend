from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers.lead_controller import LeadController
from app.db.database import get_db
from app.schemas.lead import LeadCreate, LeadRead

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=list[LeadRead], summary="Lista os leads cadastrados")
def read_leads(db: Session = Depends(get_db)) -> list[LeadRead]:
    return LeadController(db).list_leads()


@router.post(
    "",
    response_model=LeadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo lead",
)
def create_new_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> LeadRead:
    return LeadController(db).create_lead(payload)
