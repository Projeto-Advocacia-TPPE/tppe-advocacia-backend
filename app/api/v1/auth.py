from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.auth_controller import AuthController
from app.db.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, summary="Authenticate user and return JWT")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthController(db).login(payload)
