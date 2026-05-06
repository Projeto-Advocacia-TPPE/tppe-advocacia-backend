import logging
import secrets
import string
import bcrypt

from app.models.user import Role
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.utils.exceptions import EmailAlreadyExistsError, UserNotFoundError

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def list_users(
        self,
        role: Role | None,
        is_active: bool | None,
        page: int,
        limit: int,
    ) -> tuple[list[UserRead], int]:
        users, total = self.repository.get_all(
            role=role, is_active=is_active, page=page, limit=limit
        )
        return [UserRead.model_validate(u) for u in users], total

    def get_user(self, user_id: int) -> UserRead:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return UserRead.model_validate(user)

    def create_user(self, payload: UserCreate) -> UserRead:
        if self.repository.email_exists(payload.email):
            raise EmailAlreadyExistsError()

        temp_password = self._generate_password()
        hashed = bcrypt.hashpw(temp_password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

        user = self.repository.create(
            name=payload.name,
            email=payload.email,
            hashed_password=hashed,
            role=payload.role,
        )
        logger.info("Temporary password for %s: %s", payload.email, temp_password)
        return UserRead.model_validate(user)

    def update_user(self, user_id: int, payload: UserUpdate) -> UserRead:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()

        updates = payload.model_dump(exclude_none=True)

        if "email" in updates and updates["email"] != user.email:
            if self.repository.email_exists(updates["email"], exclude_id=user_id):
                raise EmailAlreadyExistsError()

        return UserRead.model_validate(self.repository.update(user, updates))

    @staticmethod
    def _generate_password(length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))
