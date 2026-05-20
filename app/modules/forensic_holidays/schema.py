from datetime import date as _date
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.forensic_holidays.model import HolidayScope


class HolidayCreate(BaseModel):
    date: _date
    description: str = Field(min_length=1, max_length=255)
    scope: HolidayScope
    court: str | None = Field(default=None, max_length=50)
    comarca: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_scope_fields(self) -> "HolidayCreate":
        _validate_scope_consistency(self.scope, self.court, self.comarca)
        return self


class HolidayUpdate(BaseModel):
    date: _date | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    scope: HolidayScope | None = None
    court: str | None = Field(default=None, max_length=50)
    comarca: str | None = Field(default=None, max_length=120)


class HolidayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: _date
    description: str
    scope: HolidayScope
    court: str | None
    comarca: str | None
    created_at: datetime
    updated_at: datetime


def _validate_scope_consistency(
    scope: HolidayScope, court: str | None, comarca: str | None
) -> None:
    from app.shared.exceptions import InvalidHolidayScopeError

    if scope == HolidayScope.NATIONAL and (court or comarca):
        raise InvalidHolidayScopeError(
            "NATIONAL scope must not include court or comarca"
        )
    if scope == HolidayScope.COURT and not court:
        raise InvalidHolidayScopeError("COURT scope requires court")
    if scope == HolidayScope.COURT and comarca:
        raise InvalidHolidayScopeError("COURT scope must not include comarca")
    if scope == HolidayScope.COMARCA and not comarca:
        raise InvalidHolidayScopeError("COMARCA scope requires comarca")
