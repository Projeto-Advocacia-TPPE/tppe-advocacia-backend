from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.database import get_db
from app.modules.email.protocol import EmailService
from app.modules.tasks.controller import TaskController
from app.modules.tasks.model import TaskPriority, TaskStatus
from app.modules.tasks.schema import (
    KanbanColumn,
    KanbanRead,
    TaskCreate,
    TaskMove,
    TaskRead,
    TaskUpdate,
)
from app.modules.users.model import User
from app.shared.auth_deps import get_current_user
from app.shared.email_deps import get_email_service
from app.shared.responses import (
    PaginatedResponse,
    SuccessResponse,
    error_responses,
    ok,
    paginated,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[TaskRead],
    responses=error_responses(401, 422),
    summary="Create a new task",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[TaskRead]:
    task = TaskController(db, email).create_task(payload, created_by=current_user)
    return ok(TaskRead.model_validate(task))


@router.get(
    "",
    response_model=PaginatedResponse[TaskRead],
    responses=error_responses(401),
    summary="List tasks with filters and pagination",
)
def list_tasks(
    assigned_to: int | None = Query(None),
    status: TaskStatus | None = Query(None),
    priority: TaskPriority | None = Query(None),
    client_id: int | None = Query(None),
    process_id: int | None = Query(None),
    due_date_from: datetime | None = Query(None),
    due_date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[TaskRead]:
    items, total = TaskController(db, email).list_tasks(
        assigned_to=assigned_to,
        status=status,
        priority=priority,
        client_id=client_id,
        process_id=process_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        page=page,
        limit=limit,
    )
    return paginated(
        [TaskRead.model_validate(t) for t in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get(
    "/kanban",
    response_model=SuccessResponse[KanbanRead],
    responses=error_responses(401),
    summary="Get tasks grouped by status (Kanban view)",
)
def get_kanban(
    assigned_to: int | None = Query(None),
    client_id: int | None = Query(None),
    process_id: int | None = Query(None),
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_user),
) -> SuccessResponse[KanbanRead]:
    grouped = TaskController(db, email).get_kanban_view(
        assigned_to=assigned_to,
        client_id=client_id,
        process_id=process_id,
        max_per_column=settings.kanban_max_per_column,
    )
    columns = {
        status.value: KanbanColumn(
            items=[TaskRead.model_validate(t) for t in items],
            total=total,
            has_more=total > len(items),
        )
        for status, (items, total) in grouped.items()
    }
    return ok(KanbanRead(**columns))


@router.get(
    "/{task_id}",
    response_model=SuccessResponse[TaskRead],
    responses=error_responses(401, 404),
    summary="Get a task by ID",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    _: User = Depends(get_current_user),
) -> SuccessResponse[TaskRead]:
    task = TaskController(db, email).get_task(task_id)
    return ok(TaskRead.model_validate(task))


@router.patch(
    "/{task_id}",
    response_model=SuccessResponse[TaskRead],
    responses=error_responses(401, 404, 422),
    summary="Partially update a task",
)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[TaskRead]:
    task = TaskController(db, email).update_task(
        task_id, payload, updated_by=current_user
    )
    return ok(TaskRead.model_validate(task))


@router.patch(
    "/{task_id}/move",
    response_model=SuccessResponse[TaskRead],
    responses=error_responses(401, 404, 422),
    summary="Move a task between columns (Kanban) with atomic reorder",
)
def move_task(
    task_id: int,
    payload: TaskMove,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[TaskRead]:
    task = TaskController(db, email).move_task(
        task_id, payload, updated_by=current_user
    )
    return ok(TaskRead.model_validate(task))


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404),
    summary="Delete a task (admin or creator only)",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    current_user: User = Depends(get_current_user),
) -> None:
    TaskController(db, email).delete_task(task_id, current_user=current_user)
