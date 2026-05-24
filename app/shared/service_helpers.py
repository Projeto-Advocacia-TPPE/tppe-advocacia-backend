from collections.abc import Callable
from typing import TypeVar

from app.modules.users.model import User
from app.shared.exceptions import AppException, ForbiddenError
from app.shared.types import Role

T = TypeVar("T")


def get_or_raise(loader: Callable[[], T | None], exc: type[AppException]) -> T:
    obj = loader()
    if obj is None:
        raise exc()
    return obj


def assert_author_or_admin(actor: User, owner_id: int | None) -> None:
    if actor.role == Role.ADMIN:
        return
    if owner_id is not None and owner_id == actor.id:
        return
    raise ForbiddenError()


def ensure_exists(
    repo_get: Callable[[int], object | None],
    entity_id: int | None,
    exc: type[AppException],
) -> None:
    if entity_id is not None and repo_get(entity_id) is None:
        raise exc()
