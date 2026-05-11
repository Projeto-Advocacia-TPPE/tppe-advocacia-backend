from sqlalchemy.orm import Session

from app.modules.auth.schema import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.email.protocol import EmailService


class AuthController:
    def __init__(self, db: Session) -> None:
        self.service = AuthService(db)

    def login(self, payload: LoginRequest) -> TokenResponse:
        return self.service.login(payload)

    def request_password_reset(
        self, payload: PasswordResetRequest, email_service: EmailService
    ) -> None:
        self.service.request_reset(payload, email_service)

    def confirm_password_reset(self, payload: PasswordResetConfirm) -> None:
        self.service.confirm_reset(payload)
