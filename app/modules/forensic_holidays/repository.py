from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.forensic_holidays.model import ForensicHoliday, HolidayScope


class ForensicHolidayRepository:
    """Este repositório nunca comita. Operações de escrita usam db.add + db.flush
    e o Service que orquestra a transação fecha com unit_of_work."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        date_: date,
        description: str,
        scope: HolidayScope,
        court: str | None,
        comarca: str | None,
    ) -> ForensicHoliday:
        holiday = ForensicHoliday(
            date=date_,
            description=description,
            scope=scope,
            court=court,
            comarca=comarca,
        )
        self.db.add(holiday)
        self.db.flush()
        return holiday

    def get_by_id(self, holiday_id: int) -> ForensicHoliday | None:
        return self.db.scalars(
            select(ForensicHoliday).where(ForensicHoliday.id == holiday_id)
        ).first()

    def get_by_natural_key(
        self,
        date_: date,
        scope: HolidayScope,
        court: str | None,
        comarca: str | None,
    ) -> ForensicHoliday | None:
        stmt = select(ForensicHoliday).where(
            ForensicHoliday.date == date_,
            ForensicHoliday.scope == scope,
            ForensicHoliday.court.is_(court)
            if court is None
            else ForensicHoliday.court == court,
            ForensicHoliday.comarca.is_(comarca)
            if comarca is None
            else ForensicHoliday.comarca == comarca,
        )
        return self.db.scalars(stmt).first()

    def update(
        self,
        holiday: ForensicHoliday,
        date_: date | None,
        description: str | None,
        scope: HolidayScope | None,
        court: str | None,
        comarca: str | None,
        clear_court: bool,
        clear_comarca: bool,
    ) -> ForensicHoliday:
        if date_ is not None:
            holiday.date = date_
        if description is not None:
            holiday.description = description
        if scope is not None:
            holiday.scope = scope
        if court is not None:
            holiday.court = court
        elif clear_court:
            holiday.court = None
        if comarca is not None:
            holiday.comarca = comarca
        elif clear_comarca:
            holiday.comarca = None
        self.db.flush()
        return holiday

    def delete(self, holiday: ForensicHoliday) -> None:
        self.db.delete(holiday)
        self.db.flush()

    def list(
        self,
        year: int | None,
        court: str | None,
        comarca: str | None,
        page: int = 1,
        limit: int = 100,
    ) -> tuple[list[ForensicHoliday], int]:
        base = select(ForensicHoliday)
        conditions = []

        if year is not None:
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            conditions.append(
                and_(ForensicHoliday.date >= start, ForensicHoliday.date <= end)
            )

        if court is not None or comarca is not None:
            scope_filters = [ForensicHoliday.scope == HolidayScope.NATIONAL]
            if court is not None:
                scope_filters.append(
                    and_(
                        ForensicHoliday.scope == HolidayScope.COURT,
                        ForensicHoliday.court == court,
                    )
                )
            if comarca is not None:
                scope_filters.append(
                    and_(
                        ForensicHoliday.scope == HolidayScope.COMARCA,
                        ForensicHoliday.comarca == comarca,
                    )
                )
            conditions.append(or_(*scope_filters))

        if conditions:
            base = base.where(and_(*conditions))

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.order_by(ForensicHoliday.date.asc(), ForensicHoliday.id.asc())
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()
        )
        return items, total

    def list_applicable_in_range(
        self,
        start: date,
        end: date,
        court: str | None,
        comarca: str | None,
    ) -> list[ForensicHoliday]:
        scope_filters = [ForensicHoliday.scope == HolidayScope.NATIONAL]
        if court is not None:
            scope_filters.append(
                and_(
                    ForensicHoliday.scope == HolidayScope.COURT,
                    ForensicHoliday.court == court,
                )
            )
        if comarca is not None:
            scope_filters.append(
                and_(
                    ForensicHoliday.scope == HolidayScope.COMARCA,
                    ForensicHoliday.comarca == comarca,
                )
            )

        stmt = (
            select(ForensicHoliday)
            .where(
                ForensicHoliday.date >= start,
                ForensicHoliday.date <= end,
                or_(*scope_filters),
            )
            .order_by(ForensicHoliday.date.asc())
        )
        return list(self.db.scalars(stmt).all())
