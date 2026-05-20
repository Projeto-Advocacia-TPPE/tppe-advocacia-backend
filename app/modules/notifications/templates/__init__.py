from collections.abc import Callable

from app.modules.notifications.schema import EventType
from app.modules.notifications.templates import (
    deadline_approaching,
    deadline_expired,
    external_api_failure,
    lead_assigned,
    process_movement_created,
    process_status_changed,
    task_assigned,
)

Renderer = Callable[[dict], tuple[str, str]]

TEMPLATES: dict[EventType, Renderer] = {
    EventType.PROCESS_MOVEMENT_CREATED: process_movement_created.render,
    EventType.PROCESS_STATUS_CHANGED: process_status_changed.render,
    EventType.LEAD_ASSIGNED: lead_assigned.render,
    EventType.TASK_ASSIGNED: task_assigned.render,
    EventType.DEADLINE_APPROACHING: deadline_approaching.render,
    EventType.DEADLINE_EXPIRED: deadline_expired.render,
    EventType.EXTERNAL_API_FAILURE: external_api_failure.render,
}
