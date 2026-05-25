from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.auth.service import AuthService
from app.modules.email.protocol import EmailService
from app.modules.users.repository import UserRepository
from app.shared.deps.email import get_email_service


def get_auth_service(
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
) -> AuthService:
    return AuthService(UserRepository(db), email)
