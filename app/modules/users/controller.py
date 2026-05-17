from sqlalchemy.orm import Session

from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.audit_logs.service import AuditLogService
from app.modules.email.protocol import EmailService
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate, UserRead, UserUpdate
from app.modules.users.service import UserService
from app.shared.types import Role


class UserController:
    def __init__(self, db: Session, email: EmailService) -> None:
        self.service = UserService(
            UserRepository(db),
            email,
            AuditLogService(AuditLogRepository(db)),
        )

    def list_users(
        self,
        role: Role | None,
        is_active: bool | None,
        page: int,
        limit: int,
    ) -> tuple[list[UserRead], int]:
        return self.service.list_users(
            role=role, is_active=is_active, page=page, limit=limit
        )

    def get_user(self, user_id: int) -> UserRead:
        return self.service.get_user(user_id)

    def create_user(self, payload: UserCreate, created_by: User) -> UserRead:
        return self.service.create_user(payload, created_by=created_by)

    def update_user(
        self, user_id: int, payload: UserUpdate, updated_by: User
    ) -> UserRead:
        return self.service.update_user(user_id, payload, updated_by=updated_by)
