from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.modules.notifications.schema import EventType
from app.modules.tasks.model import Task, TaskPriority, TaskStatus
from app.modules.tasks.schema import TaskCreate, TaskMove, TaskUpdate
from app.modules.tasks.service import TaskService
from app.shared.exceptions import (
    AssigneeNotFoundError,
    ForbiddenError,
    TaskClientNotFoundError,
    TaskNotFoundError,
    TaskProcessNotFoundError,
)
from app.shared.types import Role


def make_task(**kwargs) -> Task:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "title": "T",
        "description": None,
        "due_date": None,
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.TODO,
        "order": 0,
        "assigned_to": None,
        "client_id": None,
        "process_id": None,
        "created_by": 10,
        "updated_by": 10,
        "completed_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    task = MagicMock(spec=Task)
    for k, v in defaults.items():
        setattr(task, k, v)
    return task


def make_user(*, id=10, role=Role.USER):
    user = MagicMock()
    user.id = id
    user.role = role
    return user


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def clients():
    return MagicMock()


@pytest.fixture
def processes():
    return MagicMock()


@pytest.fixture
def users():
    return MagicMock()


@pytest.fixture
def notifications():
    return MagicMock()


@pytest.fixture
def service(repo, clients, processes, users, notifications):
    svc = TaskService.__new__(TaskService)
    svc.repository = repo
    svc.clients = clients
    svc.processes = processes
    svc.users = users
    svc.notifications = notifications
    return svc


class TestCreateTask:
    def test_creates_with_defaults(self, service, repo):
        created = make_task()
        repo.create.return_value = created
        payload = TaskCreate(title="X")

        result = service.create_task(payload, created_by=make_user())

        assert result is created
        repo.create.assert_called_once()
        kwargs = repo.create.call_args.kwargs
        assert kwargs["status"] == TaskStatus.TODO
        assert kwargs["priority"] == TaskPriority.MEDIUM

    def test_validates_assignee_exists(self, service, users):
        users.get_by_id.return_value = None
        with pytest.raises(AssigneeNotFoundError):
            service.create_task(
                TaskCreate(title="X", assigned_to=99), created_by=make_user()
            )

    def test_validates_client_exists(self, service, clients):
        clients.get_by_id.return_value = None
        with pytest.raises(TaskClientNotFoundError):
            service.create_task(
                TaskCreate(title="X", client_id=99), created_by=make_user()
            )

    def test_validates_process_exists(self, service, processes):
        processes.get_by_id.return_value = None
        with pytest.raises(TaskProcessNotFoundError):
            service.create_task(
                TaskCreate(title="X", process_id=99), created_by=make_user()
            )

    def test_dispatches_notification_when_assignee_set(
        self, service, repo, users, notifications
    ):
        users.get_by_id.return_value = MagicMock()
        created = make_task(assigned_to=5, title="Revisar")
        repo.create.return_value = created

        service.create_task(
            TaskCreate(title="Revisar", assigned_to=5), created_by=make_user()
        )

        notifications.notify.assert_called_once()
        assert notifications.notify.call_args.kwargs["user_id"] == 5
        assert (
            notifications.notify.call_args.kwargs["event_type"]
            == EventType.TASK_ASSIGNED
        )

    def test_does_not_notify_when_unassigned(self, service, repo, notifications):
        repo.create.return_value = make_task(assigned_to=None)
        service.create_task(TaskCreate(title="X"), created_by=make_user())
        notifications.notify.assert_not_called()

    def test_does_not_notify_when_self_assigned(
        self, service, repo, users, notifications
    ):
        users.get_by_id.return_value = MagicMock()
        repo.create.return_value = make_task(assigned_to=10)

        service.create_task(
            TaskCreate(title="X", assigned_to=10),
            created_by=make_user(id=10),
        )

        notifications.notify.assert_not_called()


class TestGetTask:
    def test_returns_task(self, service, repo):
        task = make_task()
        repo.get_by_id.return_value = task
        assert service.get_task(1) is task

    def test_raises_when_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(TaskNotFoundError):
            service.get_task(99)


class TestUpdateTask:
    def test_notifies_when_assignee_changes(self, service, repo, users, notifications):
        old = make_task(assigned_to=1)
        new = make_task(assigned_to=2)
        repo.get_by_id.return_value = old
        repo.update.return_value = new
        users.get_by_id.return_value = MagicMock()

        service.update_task(1, TaskUpdate(assigned_to=2), updated_by=make_user())

        notifications.notify.assert_called_once()
        assert notifications.notify.call_args.kwargs["user_id"] == 2

    def test_does_not_notify_when_assignee_unchanged(
        self, service, repo, notifications
    ):
        task = make_task(assigned_to=1)
        repo.get_by_id.return_value = task
        repo.update.return_value = task

        service.update_task(1, TaskUpdate(title="novo"), updated_by=make_user())

        notifications.notify.assert_not_called()

    def test_does_not_notify_when_assignee_cleared(self, service, repo, notifications):
        old = make_task(assigned_to=1)
        new = make_task(assigned_to=None)
        repo.get_by_id.return_value = old
        repo.update.return_value = new

        service.update_task(1, TaskUpdate(assigned_to=None), updated_by=make_user())

        notifications.notify.assert_not_called()

    def test_does_not_notify_when_self_assign_on_update(
        self, service, repo, users, notifications
    ):
        users.get_by_id.return_value = MagicMock()
        old = make_task(assigned_to=None)
        new = make_task(assigned_to=42)
        repo.get_by_id.return_value = old
        repo.update.return_value = new

        service.update_task(
            1, TaskUpdate(assigned_to=42), updated_by=make_user(id=42)
        )

        notifications.notify.assert_not_called()


class TestMoveTask:
    def test_delegates_to_repository(self, service, repo):
        task = make_task()
        moved = make_task(status=TaskStatus.DONE, order=0)
        repo.get_by_id.return_value = task
        repo.move.return_value = moved

        result = service.move_task(
            1, TaskMove(status=TaskStatus.DONE, order=0), updated_by=make_user()
        )

        assert result is moved
        repo.move.assert_called_once_with(
            task, new_status=TaskStatus.DONE, new_order=0, updated_by=10
        )


class TestGetKanbanView:
    def test_delegates_to_repository_with_filters(self, service, repo):
        repo.list_kanban.return_value = {s: ([], 0) for s in TaskStatus}

        service.get_kanban_view(
            assigned_to=5, client_id=7, process_id=9, max_per_column=50
        )

        repo.list_kanban.assert_called_once_with(
            assigned_to=5, client_id=7, process_id=9, max_per_column=50
        )

    def test_returns_repository_result(self, service, repo):
        expected = {s: ([make_task()], 1) for s in TaskStatus}
        repo.list_kanban.return_value = expected

        result = service.get_kanban_view(max_per_column=100)

        assert result is expected


class TestDeleteTask:
    def test_creator_can_delete(self, service, repo):
        task = make_task(created_by=10)
        repo.get_by_id.return_value = task
        service.delete_task(1, current_user=make_user(id=10))
        repo.delete.assert_called_once_with(task)

    def test_admin_can_delete_others_task(self, service, repo):
        task = make_task(created_by=5)
        repo.get_by_id.return_value = task
        service.delete_task(1, current_user=make_user(id=99, role=Role.ADMIN))
        repo.delete.assert_called_once()

    def test_non_admin_non_creator_forbidden(self, service, repo):
        task = make_task(created_by=5)
        repo.get_by_id.return_value = task
        with pytest.raises(ForbiddenError):
            service.delete_task(1, current_user=make_user(id=99, role=Role.USER))
        repo.delete.assert_not_called()
