from sqlalchemy.orm import Session

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService


class AuthController:
    def __init__(self, db: Session) -> None:
        self.service = AuthService(db)

    def login(self, payload: LoginRequest) -> TokenResponse:
        return self.service.login(payload)
