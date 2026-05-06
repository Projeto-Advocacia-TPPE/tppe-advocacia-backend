from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse

settings = get_settings()

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

_INACTIVE_USER = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Inactive user",
)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.repository.get_by_email(payload.email)

        if user is None:
            raise _INVALID_CREDENTIALS

        password_matches = bcrypt.checkpw(
            payload.password.encode("utf-8"),
            user.hashed_password.encode("utf-8"),
        )
        if not password_matches:
            raise _INVALID_CREDENTIALS

        if not user.is_active:
            raise _INACTIVE_USER

        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": expire,
        }
        token = jwt.encode(token_data, settings.jwt_secret_key, algorithm="HS256")

        return TokenResponse(access_token=token)
