from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.modules.auth.schema import LoginRequest, TokenResponse
from app.modules.users.repository import UserRepository
from app.shared.exceptions import InactiveUserError, InvalidCredentialsError

settings = get_settings()


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.repository.get_by_email(payload.email)

        if user is None:
            raise InvalidCredentialsError()

        password_matches = bcrypt.checkpw(
            payload.password.encode("utf-8"),
            user.hashed_password.encode("utf-8"),
        )
        if not password_matches:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": expire,
        }
        token = jwt.encode(token_data, settings.jwt_secret_key, algorithm="HS256")

        return TokenResponse(access_token=token)
