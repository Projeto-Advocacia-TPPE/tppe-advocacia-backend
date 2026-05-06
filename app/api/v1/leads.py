from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers.lead_controller import LeadController
from app.db.database import get_db
from app.schemas.lead import LeadCreate, LeadRead
from app.utils.responses import SuccessResponse, error_responses, ok

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get(
    "",
    response_model=SuccessResponse[list[LeadRead]],
    responses=error_responses(422),
    summary="Lista os leads cadastrados",
)
def read_leads(db: Session = Depends(get_db)) -> SuccessResponse[list[LeadRead]]:
    return ok(LeadController(db).list_leads())


@router.post(
    "",
    response_model=SuccessResponse[LeadRead],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(422),
    summary="Cria um novo lead",
)
def create_new_lead(
    payload: LeadCreate, db: Session = Depends(get_db)
) -> SuccessResponse[LeadRead]:
    return ok(LeadController(db).create_lead(payload))
