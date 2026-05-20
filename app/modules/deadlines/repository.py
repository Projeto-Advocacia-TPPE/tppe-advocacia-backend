from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.deadlines.model import Deadline, DeadlineAlert


class DeadlineRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        process_id: int,
        start_date: date,
        business_days: int,
        deadline_type: str,
        due_date: date,
        court: str | None,
        comarca: str | None,
        created_by: int | None,
    ) -> Deadline:
        deadline = Deadline(
            process_id=process_id,
            start_date=start_date,
            business_days=business_days,
            deadline_type=deadline_type,
            due_date=due_date,
            court=court,
            comarca=comarca,
            created_by=created_by,
        )
        self.db.add(deadline)
        self.db.commit()
        self.db.refresh(deadline)
        return deadline

    def get_by_id(self, deadline_id: int) -> Deadline | None:
        return self.db.scalars(
            select(Deadline).where(Deadline.id == deadline_id)
        ).first()

    def list_by_process(
        self, process_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[Deadline], int]:
        base = select(Deadline).where(Deadline.process_id == process_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.order_by(Deadline.due_date.asc(), Deadline.id.asc())
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()
        )
        return items, total

    def update(
        self,
        deadline: Deadline,
        start_date: date | None,
        business_days: int | None,
        deadline_type: str | None,
        comarca: str | None,
        due_date: date | None,
        clear_comarca: bool,
    ) -> Deadline:
        if start_date is not None:
            deadline.start_date = start_date
        if business_days is not None:
            deadline.business_days = business_days
        if deadline_type is not None:
            deadline.deadline_type = deadline_type
        if comarca is not None:
            deadline.comarca = comarca
        elif clear_comarca:
            deadline.comarca = None
        if due_date is not None:
            deadline.due_date = due_date
        self.db.commit()
        self.db.refresh(deadline)
        return deadline

    def list_all(self) -> list[Deadline]:
        return list(self.db.scalars(select(Deadline)).all())

    def delete(self, deadline: Deadline) -> None:
        self.db.delete(deadline)
        self.db.commit()


class DeadlineAlertRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def sent_days_for(self, deadline_id: int) -> set[int]:
        return set(
            self.db.scalars(
                select(DeadlineAlert.days_before).where(
                    DeadlineAlert.deadline_id == deadline_id
                )
            ).all()
        )

    def create(self, deadline_id: int, days_before: int) -> DeadlineAlert:
        alert = DeadlineAlert(deadline_id=deadline_id, days_before=days_before)
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_by_deadline(self, deadline_id: int) -> list[DeadlineAlert]:
        return list(
            self.db.scalars(
                select(DeadlineAlert)
                .where(DeadlineAlert.deadline_id == deadline_id)
                .order_by(DeadlineAlert.sent_at.asc(), DeadlineAlert.id.asc())
            ).all()
        )
