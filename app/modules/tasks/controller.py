from sqlalchemy.orm import Session

from app.modules.clients.repository import ClientRepository
from app.modules.email.protocol import EmailService
from app.modules.notifications.repository import NotificationPreferenceRepository
from app.modules.notifications.service import NotificationService
from app.modules.processes.repository import ProcessRepository
from app.modules.tasks.model import Task, TaskStatus
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskCreate, TaskMove, TaskUpdate
from app.modules.tasks.service import TaskService
from app.modules.users.model import User
from app.modules.users.repository import UserRepository


class TaskController:
    def __init__(self, db: Session, email: EmailService) -> None:
        users_repo = UserRepository(db)
        self.service = TaskService(
            TaskRepository(db),
            ClientRepository(db),
            ProcessRepository(db),
            users_repo,
            NotificationService(
                NotificationPreferenceRepository(db),
                users_repo,
                email,
            ),
        )

    def create_task(self, payload: TaskCreate, created_by: User) -> Task:
        return self.service.create_task(payload, created_by=created_by)

    def list_tasks(self, **filters) -> tuple[list[Task], int]:
        return self.service.list_tasks(**filters)

    def get_kanban_view(
        self,
        *,
        assigned_to: int | None,
        client_id: int | None,
        process_id: int | None,
        max_per_column: int,
    ) -> dict[TaskStatus, tuple[list[Task], int]]:
        return self.service.get_kanban_view(
            assigned_to=assigned_to,
            client_id=client_id,
            process_id=process_id,
            max_per_column=max_per_column,
        )

    def get_task(self, task_id: int) -> Task:
        return self.service.get_task(task_id)

    def update_task(self, task_id: int, payload: TaskUpdate, updated_by: User) -> Task:
        return self.service.update_task(task_id, payload, updated_by=updated_by)

    def move_task(self, task_id: int, payload: TaskMove, updated_by: User) -> Task:
        return self.service.move_task(task_id, payload, updated_by=updated_by)

    def delete_task(self, task_id: int, current_user: User) -> None:
        self.service.delete_task(task_id, current_user=current_user)
