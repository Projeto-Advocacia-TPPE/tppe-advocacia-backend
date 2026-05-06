from sqlalchemy.orm import Session

from app.models.user import Role
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserListResponse, UserRead, UserUpdate
from app.services.user_service import UserService


class UserController:
    def __init__(self, db: Session) -> None:
        self.service = UserService(UserRepository(db))

    def list_users(
        self,
        role: Role | None,
        is_active: bool | None,
        page: int,
        limit: int,
    ) -> UserListResponse:
        return self.service.list_users(
            role=role, is_active=is_active, page=page, limit=limit
        )

    def get_user(self, user_id: int) -> UserRead:
        return self.service.get_user(user_id)

    def create_user(self, payload: UserCreate) -> UserRead:
        return self.service.create_user(payload)

    def update_user(self, user_id: int, payload: UserUpdate) -> UserRead:
        return self.service.update_user(user_id, payload)
