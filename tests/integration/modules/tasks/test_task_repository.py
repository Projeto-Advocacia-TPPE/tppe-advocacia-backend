from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.tasks.model import Task, TaskPriority, TaskStatus
from app.modules.tasks.repository import TaskRepository
from app.modules.users.repository import UserRepository
from app.shared.types import Role


def make_user(db: Session, email: str = "u@test.com"):
    return UserRepository(db).create(
        name="U", email=email, hashed_password="h", role=Role.USER
    )


def make_task(repo: TaskRepository, user_id: int, *, title="T", status=TaskStatus.TODO):
    return repo.create(
        title=title,
        description=None,
        due_date=None,
        priority=TaskPriority.MEDIUM,
        status=status,
        assigned_to=None,
        client_id=None,
        process_id=None,
        created_by=user_id,
    )


def fetch_ordered(db: Session, status: TaskStatus) -> list[tuple[int, int]]:
    rows = (
        db.query(Task.id, Task.order)
        .filter(Task.status == status)
        .order_by(Task.order)
        .all()
    )
    return [(r[0], r[1]) for r in rows]


class TestCreate:
    def test_first_task_gets_order_zero(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        task = make_task(repo, user.id)
        assert task.order == 0

    def test_subsequent_tasks_increment_order(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        t1 = make_task(repo, user.id)
        t2 = make_task(repo, user.id)
        t3 = make_task(repo, user.id)
        assert (t1.order, t2.order, t3.order) == (0, 1, 2)

    def test_order_is_per_status(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        todo = make_task(repo, user.id, status=TaskStatus.TODO)
        in_prog = make_task(repo, user.id, status=TaskStatus.IN_PROGRESS)
        assert todo.order == 0
        assert in_prog.order == 0


class TestList:
    def test_filters_by_assigned_to(self, db: Session):
        u1 = make_user(db, "a@test.com")
        u2 = make_user(db, "b@test.com")
        repo = TaskRepository(db)
        repo.create(
            title="t1",
            description=None,
            due_date=None,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.TODO,
            assigned_to=u1.id,
            client_id=None,
            process_id=None,
            created_by=u1.id,
        )
        make_task(repo, u2.id)

        items, total = repo.list(assigned_to=u1.id)
        assert total == 1
        assert items[0].assigned_to == u1.id

    def test_filters_by_due_date_range(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        now = datetime.now(timezone.utc)
        repo.create(
            title="past",
            description=None,
            due_date=now - timedelta(days=2),
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.TODO,
            assigned_to=None,
            client_id=None,
            process_id=None,
            created_by=user.id,
        )
        repo.create(
            title="future",
            description=None,
            due_date=now + timedelta(days=2),
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.TODO,
            assigned_to=None,
            client_id=None,
            process_id=None,
            created_by=user.id,
        )

        items, total = repo.list(due_date_from=now)
        assert total == 1
        assert items[0].title == "future"


class TestMoveWithinColumn:
    def test_move_down(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        a = make_task(repo, user.id, title="a")
        b = make_task(repo, user.id, title="b")
        c = make_task(repo, user.id, title="c")
        d = make_task(repo, user.id, title="d")

        repo.move(a, new_status=TaskStatus.TODO, new_order=2, updated_by=user.id)

        ordered = fetch_ordered(db, TaskStatus.TODO)
        assert ordered == [(b.id, 0), (c.id, 1), (a.id, 2), (d.id, 3)]

    def test_move_up(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        a = make_task(repo, user.id, title="a")
        b = make_task(repo, user.id, title="b")
        c = make_task(repo, user.id, title="c")
        d = make_task(repo, user.id, title="d")

        repo.move(d, new_status=TaskStatus.TODO, new_order=1, updated_by=user.id)

        ordered = fetch_ordered(db, TaskStatus.TODO)
        assert ordered == [(a.id, 0), (d.id, 1), (b.id, 2), (c.id, 3)]

    def test_move_to_same_position_is_noop(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        a = make_task(repo, user.id, title="a")
        b = make_task(repo, user.id, title="b")

        repo.move(a, new_status=TaskStatus.TODO, new_order=0, updated_by=user.id)

        assert fetch_ordered(db, TaskStatus.TODO) == [(a.id, 0), (b.id, 1)]

    def test_clamps_order_to_max(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        a = make_task(repo, user.id, title="a")
        b = make_task(repo, user.id, title="b")

        repo.move(a, new_status=TaskStatus.TODO, new_order=999, updated_by=user.id)

        assert fetch_ordered(db, TaskStatus.TODO) == [(b.id, 0), (a.id, 1)]


class TestMoveAcrossColumns:
    def test_moves_and_renumbers_source(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        a = make_task(repo, user.id, title="a")
        b = make_task(repo, user.id, title="b")
        c = make_task(repo, user.id, title="c")

        repo.move(b, new_status=TaskStatus.IN_PROGRESS, new_order=0, updated_by=user.id)

        assert fetch_ordered(db, TaskStatus.TODO) == [(a.id, 0), (c.id, 1)]
        assert fetch_ordered(db, TaskStatus.IN_PROGRESS) == [(b.id, 0)]

    def test_inserts_at_middle_of_target(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        t1 = make_task(repo, user.id, status=TaskStatus.TODO, title="t1")
        i1 = make_task(repo, user.id, status=TaskStatus.IN_PROGRESS, title="i1")
        i2 = make_task(repo, user.id, status=TaskStatus.IN_PROGRESS, title="i2")

        repo.move(
            t1, new_status=TaskStatus.IN_PROGRESS, new_order=1, updated_by=user.id
        )

        assert fetch_ordered(db, TaskStatus.IN_PROGRESS) == [
            (i1.id, 0),
            (t1.id, 1),
            (i2.id, 2),
        ]

    def test_moving_to_done_sets_completed_at(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        task = make_task(repo, user.id)

        moved = repo.move(
            task, new_status=TaskStatus.DONE, new_order=0, updated_by=user.id
        )

        assert moved.completed_at is not None

    def test_moving_out_of_done_clears_completed_at(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        task = make_task(repo, user.id)
        repo.move(task, new_status=TaskStatus.DONE, new_order=0, updated_by=user.id)

        again = repo.move(
            task, new_status=TaskStatus.TODO, new_order=0, updated_by=user.id
        )

        assert again.completed_at is None


class TestUpdate:
    def test_status_change_via_update_renumbers(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        a = make_task(repo, user.id, title="a")
        b = make_task(repo, user.id, title="b")
        c = make_task(repo, user.id, title="c")

        updated = repo.update(b, {"status": TaskStatus.DONE}, updated_by=user.id)

        assert fetch_ordered(db, TaskStatus.TODO) == [(a.id, 0), (c.id, 1)]
        done = fetch_ordered(db, TaskStatus.DONE)
        assert done == [(updated.id, 0)]
        assert updated.completed_at is not None


class TestDelete:
    def test_renumbers_column_after_delete(self, db: Session):
        user = make_user(db)
        repo = TaskRepository(db)
        a = make_task(repo, user.id, title="a")
        b = make_task(repo, user.id, title="b")
        c = make_task(repo, user.id, title="c")

        repo.delete(b)

        assert fetch_ordered(db, TaskStatus.TODO) == [(a.id, 0), (c.id, 1)]
