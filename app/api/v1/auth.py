from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.auth_controller import AuthController
from app.db.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.responses import SuccessResponse, error_responses, ok

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    responses=error_responses(401, 403, 422),
    summary="Authenticate user and return JWT",
)
def login(
    payload: LoginRequest, db: Session = Depends(get_db)
) -> SuccessResponse[TokenResponse]:
    return ok(AuthController(db).login(payload))
