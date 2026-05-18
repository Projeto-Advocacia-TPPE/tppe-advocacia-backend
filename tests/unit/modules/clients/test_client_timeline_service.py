from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.modules.clients.timeline_service import ClientTimelineService
from app.modules.processes.model import MovementSource, ProcessStatus
from app.shared.exceptions import ClientNotFoundError


def make_client(**kwargs):
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "name": "Cliente",
        "email": "c@test.com",
        "phone": None,
        "cpf": "11122233344",
        "cnpj": None,
        "address": None,
        "created_by": None,
        "updated_by": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    c = MagicMock()
    for k, v in defaults.items():
        setattr(c, k, v)
    return c


def make_process(**kwargs):
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 100,
        "number": "12345678920248260100",
        "court": "TJSP",
        "action_type": "Ação",
        "status": ProcessStatus.ATIVO,
        "created_at": now,
    }
    defaults.update(kwargs)
    p = MagicMock()
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


def make_movement(**kwargs):
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 500,
        "title": "Mov",
        "occurred_at": now,
        "source": MovementSource.MANUAL,
    }
    defaults.update(kwargs)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


@pytest.fixture
def client_repo():
    return MagicMock()


@pytest.fixture
def process_repo():
    return MagicMock()


@pytest.fixture
def timeline_repo():
    return MagicMock()


@pytest.fixture
def service(client_repo, process_repo, timeline_repo):
    return ClientTimelineService(client_repo, process_repo, timeline_repo)


class TestGetTimeline:
    def test_raises_when_client_not_found(
        self, service, client_repo, process_repo, timeline_repo
    ):
        client_repo.get_by_id.return_value = None

        with pytest.raises(ClientNotFoundError):
            service.get_timeline(99)

        client_repo.list_recent_notes.assert_not_called()
        process_repo.get_processes_with_last_movement.assert_not_called()
        timeline_repo.get_recent_activity.assert_not_called()

    def test_empty_client_returns_empty_sections(
        self, service, client_repo, process_repo, timeline_repo
    ):
        client_repo.get_by_id.return_value = make_client()
        client_repo.list_recent_notes.return_value = []
        process_repo.get_processes_with_last_movement.return_value = []
        timeline_repo.get_recent_activity.return_value = []

        timeline = service.get_timeline(1)

        assert timeline.client.id == 1
        assert timeline.notes == []
        assert timeline.processes == []
        assert timeline.recent_activity == []

    def test_uses_provided_limits(
        self, service, client_repo, process_repo, timeline_repo
    ):
        client_repo.get_by_id.return_value = make_client()
        client_repo.list_recent_notes.return_value = []
        process_repo.get_processes_with_last_movement.return_value = []
        timeline_repo.get_recent_activity.return_value = []

        service.get_timeline(1, notes_limit=5, processes_limit=7, activity_limit=3)

        client_repo.list_recent_notes.assert_called_once_with(client_id=1, limit=5)
        process_repo.get_processes_with_last_movement.assert_called_once_with(
            client_id=1, limit=7
        )
        timeline_repo.get_recent_activity.assert_called_once_with(client_id=1, limit=3)

    def test_process_with_last_movement_mapped(
        self, service, client_repo, process_repo, timeline_repo
    ):
        client_repo.get_by_id.return_value = make_client()
        client_repo.list_recent_notes.return_value = []
        process = make_process(id=10, number="X")
        movement = make_movement(id=99, title="Última")
        process_repo.get_processes_with_last_movement.return_value = [
            (process, movement)
        ]
        timeline_repo.get_recent_activity.return_value = []

        timeline = service.get_timeline(1)

        assert len(timeline.processes) == 1
        ps = timeline.processes[0]
        assert ps.id == 10
        assert ps.last_movement is not None
        assert ps.last_movement.id == 99
        assert ps.last_movement.title == "Última"

    def test_process_without_movements_has_null_last_movement(
        self, service, client_repo, process_repo, timeline_repo
    ):
        client_repo.get_by_id.return_value = make_client()
        client_repo.list_recent_notes.return_value = []
        process_repo.get_processes_with_last_movement.return_value = [
            (make_process(id=10), None)
        ]
        timeline_repo.get_recent_activity.return_value = []

        timeline = service.get_timeline(1)

        assert timeline.processes[0].last_movement is None

    def test_recent_activity_items_built_from_rows(
        self, service, client_repo, process_repo, timeline_repo
    ):
        client_repo.get_by_id.return_value = make_client()
        client_repo.list_recent_notes.return_value = []
        process_repo.get_processes_with_last_movement.return_value = []
        now = datetime.now(timezone.utc)
        timeline_repo.get_recent_activity.return_value = [
            {
                "kind": "movement",
                "process_id": 1,
                "note_id": None,
                "title": "Petição",
                "content": None,
                "occurred_at": now,
                "actor_id": 7,
                "actor_name": "Ana",
            },
            {
                "kind": "client_note",
                "process_id": None,
                "note_id": 42,
                "title": None,
                "content": "obs",
                "occurred_at": now - timedelta(days=1),
                "actor_id": 7,
                "actor_name": "Ana",
            },
        ]

        timeline = service.get_timeline(1)

        assert [it.kind for it in timeline.recent_activity] == [
            "movement",
            "client_note",
        ]
        assert timeline.recent_activity[0].process_id == 1
        assert timeline.recent_activity[1].note_id == 42
