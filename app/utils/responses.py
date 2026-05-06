from math import ceil
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T


class PageMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: list[T]
    meta: PageMeta


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail


def ok(data: T) -> SuccessResponse[T]:
    return SuccessResponse(data=data)


def paginated(items: list[T], total: int, page: int, limit: int) -> PaginatedResponse[T]:
    pages = ceil(total / limit) if total else 1
    return PaginatedResponse(data=items, meta=PageMeta(total=total, page=page, limit=limit, pages=pages))


def error_responses(*codes: int) -> dict[int, dict]:
    return {code: {"model": ErrorResponse} for code in codes}
