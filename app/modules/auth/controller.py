from sqlalchemy.orm import Session

from app.modules.auth.schema import LoginRequest, TokenResponse
from app.modules.auth.service import AuthService


class AuthController:
    def __init__(self, db: Session) -> None:
        self.service = AuthService(db)

    def login(self, payload: LoginRequest) -> TokenResponse:
        return self.service.login(payload)
