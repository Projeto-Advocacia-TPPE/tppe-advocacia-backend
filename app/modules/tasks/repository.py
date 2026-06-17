from datetime import datetime, timezone

from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session, joinedload

from app.modules.tasks.model import Task, TaskPriority, TaskStatus


class TaskRepository:
    """Este repositório nunca comita. Operações de escrita usam db.add + db.flush
    e o Service que orquestra a transação fecha com unit_of_work."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _query(self):
        return select(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
        )

    def get_by_id(self, task_id: int) -> Task | None:
        return self.db.scalars(self._query().where(Task.id == task_id)).first()

    def count_in_status(self, status: TaskStatus) -> int:
        return (
            self.db.scalar(
                select(func.count()).select_from(Task).where(Task.status == status)
            )
            or 0
        )

    def _next_order(self, status: TaskStatus) -> int:
        max_order = self.db.scalar(
            select(func.max(Task.order)).where(Task.status == status)
        )
        return 0 if max_order is None else max_order + 1

    def create(
        self,
        title: str,
        description: str | None,
        due_date: datetime | None,
        priority: TaskPriority,
        status: TaskStatus,
        assigned_to: int | None,
        client_id: int | None,
        process_id: int | None,
        created_by: int,
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status=status,
            order=self._next_order(status),
            assigned_to=assigned_to,
            client_id=client_id,
            process_id=process_id,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(task)
        self.db.flush()
        return self.get_by_id(task.id)

    def update(self, task: Task, data: dict, updated_by: int) -> Task:
        old_status = task.status

        new_status = data.get("status", old_status)
        status_changing = "status" in data and new_status != old_status

        if status_changing:
            self.db.execute(
                update(Task)
                .where(and_(Task.status == old_status, Task.order > task.order))
                .values(order=Task.order - 1)
            )
            data["order"] = self._next_order(new_status)

        self._apply_completed_at(task, data, new_status, old_status)

        for key, value in data.items():
            setattr(task, key, value)
        task.updated_by = updated_by

        self.db.flush()
        return self.get_by_id(task.id)

    @staticmethod
    def _apply_completed_at(
        task: Task, data: dict, new_status: TaskStatus, old_status: TaskStatus
    ) -> None:
        if new_status == TaskStatus.DONE and old_status != TaskStatus.DONE:
            data["completed_at"] = datetime.now(timezone.utc)
        elif old_status == TaskStatus.DONE and new_status != TaskStatus.DONE:
            data["completed_at"] = None

    def move(
        self, task: Task, new_status: TaskStatus, new_order: int, updated_by: int
    ) -> Task:
        old_status = task.status
        old_order = task.order

        if old_status == new_status:
            target_size = self.count_in_status(new_status)
            new_order = min(new_order, target_size - 1)
            if new_order == old_order:
                return self.get_by_id(task.id)

            if new_order > old_order:
                self.db.execute(
                    update(Task)
                    .where(
                        and_(
                            Task.status == new_status,
                            Task.order > old_order,
                            Task.order <= new_order,
                            Task.id != task.id,
                        )
                    )
                    .values(order=Task.order - 1)
                )
            else:
                self.db.execute(
                    update(Task)
                    .where(
                        and_(
                            Task.status == new_status,
                            Task.order >= new_order,
                            Task.order < old_order,
                            Task.id != task.id,
                        )
                    )
                    .values(order=Task.order + 1)
                )
        else:
            target_size = self.count_in_status(new_status)
            new_order = min(new_order, target_size)

            self.db.execute(
                update(Task)
                .where(and_(Task.status == old_status, Task.order > old_order))
                .values(order=Task.order - 1)
            )
            self.db.execute(
                update(Task)
                .where(
                    and_(
                        Task.status == new_status,
                        Task.order >= new_order,
                        Task.id != task.id,
                    )
                )
                .values(order=Task.order + 1)
            )

            data: dict = {}
            self._apply_completed_at(task, data, new_status, old_status)
            for key, value in data.items():
                setattr(task, key, value)

        task.status = new_status
        task.order = new_order
        task.updated_by = updated_by

        self.db.flush()
        return self.get_by_id(task.id)

    def delete(self, task: Task) -> None:
        status = task.status
        order = task.order
        self.db.delete(task)
        self.db.execute(
            update(Task)
            .where(and_(Task.status == status, Task.order > order))
            .values(order=Task.order - 1)
        )
        self.db.flush()

    def list_kanban(
        self,
        *,
        assigned_to: int | None = None,
        client_id: int | None = None,
        process_id: int | None = None,
        max_per_column: int = 100,
    ) -> dict[TaskStatus, tuple[list[Task], int]]:
        base = select(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
        )

        if assigned_to is not None:
            base = base.where(Task.assigned_to == assigned_to)
        if client_id is not None:
            base = base.where(Task.client_id == client_id)
        if process_id is not None:
            base = base.where(Task.process_id == process_id)

        rows = list(
            self.db.scalars(base.order_by(Task.status, Task.order, Task.id))
            .unique()
            .all()
        )

        grouped: dict[TaskStatus, list[Task]] = {s: [] for s in TaskStatus}
        for task in rows:
            grouped[task.status].append(task)

        return {
            status: (items[:max_per_column], len(items))
            for status, items in grouped.items()
        }

    def list(
        self,
        assigned_to: int | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        client_id: int | None = None,
        process_id: int | None = None,
        due_date_from: datetime | None = None,
        due_date_to: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Task], int]:
        base = select(Task)

        if assigned_to is not None:
            base = base.where(Task.assigned_to == assigned_to)
        if status is not None:
            base = base.where(Task.status == status)
        if priority is not None:
            base = base.where(Task.priority == priority)
        if client_id is not None:
            base = base.where(Task.client_id == client_id)
        if process_id is not None:
            base = base.where(Task.process_id == process_id)
        if due_date_from is not None:
            base = base.where(Task.due_date >= due_date_from)
        if due_date_to is not None:
            base = base.where(Task.due_date <= due_date_to)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.options(
                    joinedload(Task.assignee),
                    joinedload(Task.creator),
                )
                .order_by(Task.status, Task.order, Task.id)
                .offset((page - 1) * limit)
                .limit(limit)
            )
            .unique()
            .all()
        )
        return items, total
