from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.auth.controller import AuthController
from app.modules.auth.schema import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
)
from app.modules.email.protocol import EmailService
from app.shared.email_deps import get_email_service
from app.shared.responses import SuccessResponse, error_responses, ok

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


@router.post(
    "/password-reset/request",
    response_model=SuccessResponse[None],
    responses=error_responses(422),
    summary="Request password reset email",
)
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
) -> SuccessResponse[None]:
    AuthController(db).request_password_reset(payload, email_service)
    return ok(None)


@router.post(
    "/password-reset/confirm",
    response_model=SuccessResponse[None],
    responses=error_responses(400, 422),
    summary="Confirm password reset with token",
)
def confirm_password_reset(
    payload: PasswordResetConfirm, db: Session = Depends(get_db)
) -> SuccessResponse[None]:
    AuthController(db).confirm_password_reset(payload)
    return ok(None)
