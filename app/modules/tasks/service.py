from app.modules.clients.repository import ClientRepository
from app.modules.notifications.schema import EventType
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.tasks.model import Task, TaskStatus
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskCreate, TaskMove, TaskUpdate
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.shared.exceptions import (
    AssigneeNotFoundError,
    ForbiddenError,
    TaskClientNotFoundError,
    TaskNotFoundError,
    TaskProcessNotFoundError,
)
from app.shared.types import Role


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        clients: ClientRepository,
        processes: ProcessRepository,
        users: UserRepository,
        notifications: NotificationService,
    ) -> None:
        self.repository = repository
        self.clients = clients
        self.processes = processes
        self.users = users
        self.notifications = notifications

    def create_task(self, payload: TaskCreate, created_by: User) -> Task:
        self._validate_references(
            assigned_to=payload.assigned_to,
            client_id=payload.client_id,
            process_id=payload.process_id,
        )

        task = self.repository.create(
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            priority=payload.priority,
            status=TaskStatus.TODO,
            assigned_to=payload.assigned_to,
            client_id=payload.client_id,
            process_id=payload.process_id,
            created_by=created_by.id,
        )

        if task.assigned_to is not None:
            self._notify_assignee(task, actor_id=created_by.id)
        return task

    def get_task(self, task_id: int) -> Task:
        task = self.repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError()
        return task

    def list_tasks(self, **filters) -> tuple[list[Task], int]:
        return self.repository.list(**filters)

    def get_kanban_view(
        self,
        *,
        assigned_to: int | None = None,
        client_id: int | None = None,
        process_id: int | None = None,
        max_per_column: int = 100,
    ) -> dict[TaskStatus, tuple[list[Task], int]]:
        return self.repository.list_kanban(
            assigned_to=assigned_to,
            client_id=client_id,
            process_id=process_id,
            max_per_column=max_per_column,
        )

    def update_task(self, task_id: int, payload: TaskUpdate, updated_by: User) -> Task:
        task = self.get_task(task_id)
        data = payload.model_dump(exclude_unset=True)

        self._validate_references(
            assigned_to=data.get("assigned_to"),
            client_id=data.get("client_id"),
            process_id=data.get("process_id"),
        )

        old_assignee = task.assigned_to
        new_assignee = data.get("assigned_to", old_assignee)

        updated = self.repository.update(task, data, updated_by=updated_by.id)

        if (
            "assigned_to" in data
            and new_assignee is not None
            and new_assignee != old_assignee
        ):
            self._notify_assignee(updated, actor_id=updated_by.id)

        return updated

    def move_task(self, task_id: int, payload: TaskMove, updated_by: User) -> Task:
        task = self.get_task(task_id)
        return self.repository.move(
            task,
            new_status=payload.status,
            new_order=payload.order,
            updated_by=updated_by.id,
        )

    def delete_task(self, task_id: int, current_user: User) -> None:
        task = self.get_task(task_id)
        if current_user.role != Role.ADMIN and task.created_by != current_user.id:
            raise ForbiddenError()
        self.repository.delete(task)

    def _validate_references(
        self,
        assigned_to: int | None,
        client_id: int | None,
        process_id: int | None,
    ) -> None:
        if assigned_to is not None and self.users.get_by_id(assigned_to) is None:
            raise AssigneeNotFoundError()
        if client_id is not None and self.clients.get_by_id(client_id) is None:
            raise TaskClientNotFoundError()
        if process_id is not None and self.processes.get_by_id(process_id) is None:
            raise TaskProcessNotFoundError()

    def _notify_assignee(self, task: Task, actor_id: int | None) -> None:
        if task.assigned_to is None or task.assigned_to == actor_id:
            return
        self.notifications.notify(
            user_id=task.assigned_to,
            event_type=EventType.TASK_ASSIGNED,
            payload={
                "task_id": task.id,
                "task_title": task.title,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            },
        )
