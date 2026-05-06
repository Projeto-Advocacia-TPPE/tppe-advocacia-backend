from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail


def ok(data: T) -> SuccessResponse[T]:
    return SuccessResponse(data=data)


def error_responses(*codes: int) -> dict[int, dict]:
    return {code: {"model": ErrorResponse} for code in codes}
