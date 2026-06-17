from fastapi import APIRouter, Depends, Request

from app.modules.auth.deps import get_auth_service
from app.modules.auth.schema import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.shared.http.responses import SuccessResponse, error_responses, ok
from app.shared.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    responses=error_responses(401, 403, 422),
    summary="Autentica usuário e retorna JWT",
)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse[TokenResponse]:
    return ok(service.login(payload))


@router.post(
    "/password-reset/request",
    response_model=SuccessResponse[None],
    responses=error_responses(422),
    summary="Solicita email de redefinição de senha",
)
@limiter.limit("3/minute")
def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse[None]:
    service.request_reset(payload)
    return ok(None)


@router.post(
    "/password-reset/confirm",
    response_model=SuccessResponse[None],
    responses=error_responses(400, 422),
    summary="Confirma redefinição de senha com token",
)
@limiter.limit("5/minute")
def confirm_password_reset(
    request: Request,
    payload: PasswordResetConfirm,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse[None]:
    service.confirm_reset(payload)
    return ok(None)
