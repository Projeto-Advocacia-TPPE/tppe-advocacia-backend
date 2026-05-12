from sqlalchemy.orm import Session

from app.modules.auth.schema import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.email.protocol import EmailService
from app.modules.users.repository import UserRepository


class AuthController:
    def __init__(self, db: Session, email: EmailService) -> None:
        self.service = AuthService(UserRepository(db), email)

    def login(self, payload: LoginRequest) -> TokenResponse:
        return self.service.login(payload)

    def request_password_reset(self, payload: PasswordResetRequest) -> None:
        self.service.request_reset(payload)

    def confirm_password_reset(self, payload: PasswordResetConfirm) -> None:
        self.service.confirm_reset(payload)
