from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.modules.leads.model import Lead, LeadStatus
from app.modules.leads.schema import LeadCreate, LeadUpdate
from app.modules.leads.service import LeadService
from app.shared.exceptions import (
    AssigneeNotFoundError,
    LeadDuplicateError,
    LeadNotFoundError,
)


def make_lead(**kwargs) -> Lead:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "name": "João Silva",
        "email": "joao@example.com",
        "phone": None,
        "message": "Gostaria de uma consulta",
        "status": LeadStatus.NOVO,
        "assigned_to": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    lead = MagicMock(spec=Lead)
    for key, value in defaults.items():
        setattr(lead, key, value)
    return lead


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def user_repo():
    return MagicMock()


@pytest.fixture
def notifications():
    return MagicMock()


@pytest.fixture
def service(repo, user_repo):
    svc = LeadService.__new__(LeadService)
    svc.repository = repo
    svc.user_repository = user_repo
    svc.notifications = None
    return svc


@pytest.fixture
def service_with_notifications(repo, user_repo, notifications):
    svc = LeadService.__new__(LeadService)
    svc.repository = repo
    svc.user_repository = user_repo
    svc.notifications = notifications
    return svc


def make_user(user_id: int = 1):
    user = MagicMock()
    user.id = user_id
    return user


class TestListLeads:
    def test_delegates_to_repository(self, service, repo):
        repo.get_all.return_value = ([], 0)

        result, total = service.list_leads()

        repo.get_all.assert_called_once_with(
            status=None, assigned_to=None, page=1, limit=20
        )
        assert result == []
        assert total == 0

    def test_passes_filters_through(self, service, repo):
        repo.get_all.return_value = ([], 0)

        service.list_leads(status=LeadStatus.NOVO, assigned_to=5, page=2, limit=10)

        repo.get_all.assert_called_once_with(
            status=LeadStatus.NOVO, assigned_to=5, page=2, limit=10
        )


class TestGetLead:
    def test_returns_lead_when_found(self, service, repo):
        lead = make_lead()
        repo.get_by_id.return_value = lead

        result = service.get_lead(1)

        assert result is lead

    def test_raises_when_not_found(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(LeadNotFoundError):
            service.get_lead(99)


class TestCreateLead:
    def test_creates_lead_when_no_recent_duplicate(self, service, repo):
        repo.find_recent_by_email.return_value = None
        lead = make_lead()
        repo.create.return_value = lead
        payload = LeadCreate(name="João Silva", email="joao@example.com")

        result = service.create_lead(payload)

        assert result is lead
        repo.create.assert_called_once_with(
            name="João Silva", email="joao@example.com", phone=None, message=None
        )

    def test_raises_when_duplicate_email_in_window(self, service, repo):
        repo.find_recent_by_email.return_value = make_lead()
        payload = LeadCreate(name="João Silva", email="joao@example.com")

        with pytest.raises(LeadDuplicateError):
            service.create_lead(payload)

        repo.create.assert_not_called()

    def test_checks_dedup_with_configured_window(self, service, repo):
        from app.config.settings import get_settings

        repo.find_recent_by_email.return_value = None
        repo.create.return_value = make_lead()
        payload = LeadCreate(name="João Silva", email="joao@example.com")

        service.create_lead(payload)

        expected_window = get_settings().lead_dedup_window_hours
        repo.find_recent_by_email.assert_called_once_with(
            "joao@example.com", expected_window
        )


class TestUpdateLead:
    def test_updates_status(self, service, repo):
        lead = make_lead()
        updated = make_lead(status=LeadStatus.EM_ATENDIMENTO)
        repo.get_by_id.return_value = lead
        repo.update.return_value = updated
        payload = LeadUpdate(status=LeadStatus.EM_ATENDIMENTO)

        result = service.update_lead(1, payload)

        repo.update.assert_called_once_with(lead, {"status": LeadStatus.EM_ATENDIMENTO})
        assert result is updated

    def test_assigns_responsible(self, service, repo, user_repo):
        lead = make_lead()
        updated = make_lead(assigned_to=3)
        repo.get_by_id.return_value = lead
        repo.update.return_value = updated
        user_repo.get_by_id.return_value = MagicMock()
        payload = LeadUpdate(assigned_to=3)

        result = service.update_lead(1, payload)

        repo.update.assert_called_once_with(lead, {"assigned_to": 3})
        assert result is updated

    def test_raises_when_assignee_not_found(self, service, repo, user_repo):
        lead = make_lead()
        repo.get_by_id.return_value = lead
        user_repo.get_by_id.return_value = None
        payload = LeadUpdate(assigned_to=99)

        with pytest.raises(AssigneeNotFoundError):
            service.update_lead(1, payload)

    def test_skips_update_when_payload_empty(self, service, repo):
        lead = make_lead()
        repo.get_by_id.return_value = lead
        payload = LeadUpdate()

        result = service.update_lead(1, payload)

        repo.update.assert_not_called()
        assert result is lead

    def test_raises_when_lead_not_found(self, service, repo):
        repo.get_by_id.return_value = None
        payload = LeadUpdate(status=LeadStatus.FECHADO)

        with pytest.raises(LeadNotFoundError):
            service.update_lead(99, payload)


class TestUpdateLeadNotifications:
    def test_notifies_new_assignee_when_changed(
        self, service_with_notifications, repo, user_repo, notifications
    ):
        lead = make_lead(assigned_to=None, name="João", email="j@x.com", phone=None)
        updated = make_lead(assigned_to=5, name="João", email="j@x.com", phone=None)
        repo.get_by_id.return_value = lead
        repo.update.return_value = updated
        user_repo.get_by_id.return_value = MagicMock()

        service_with_notifications.update_lead(
            1, LeadUpdate(assigned_to=5), current_user=make_user(7)
        )

        notifications.notify.assert_called_once()
        kwargs = notifications.notify.call_args.kwargs
        assert kwargs["user_id"] == 5
        assert kwargs["event_type"].value == "LEAD_ASSIGNED"
        assert kwargs["payload"]["lead_id"] == 1
        assert kwargs["payload"]["lead_name"] == "João"

    def test_does_not_notify_when_self_assigning(
        self, service_with_notifications, repo, user_repo, notifications
    ):
        lead = make_lead(assigned_to=None)
        updated = make_lead(assigned_to=7)
        repo.get_by_id.return_value = lead
        repo.update.return_value = updated
        user_repo.get_by_id.return_value = MagicMock()

        service_with_notifications.update_lead(
            1, LeadUpdate(assigned_to=7), current_user=make_user(7)
        )

        notifications.notify.assert_not_called()

    def test_does_not_notify_when_assignee_unchanged(
        self, service_with_notifications, repo, notifications
    ):
        lead = make_lead(assigned_to=5)
        repo.get_by_id.return_value = lead
        repo.update.return_value = lead

        service_with_notifications.update_lead(
            1, LeadUpdate(status=LeadStatus.EM_ATENDIMENTO), current_user=make_user(7)
        )

        notifications.notify.assert_not_called()

    def test_does_not_notify_when_only_status_changes(
        self, service_with_notifications, repo, notifications
    ):
        lead = make_lead(assigned_to=None)
        repo.get_by_id.return_value = lead
        repo.update.return_value = lead

        service_with_notifications.update_lead(
            1, LeadUpdate(status=LeadStatus.FECHADO), current_user=make_user(7)
        )

        notifications.notify.assert_not_called()
