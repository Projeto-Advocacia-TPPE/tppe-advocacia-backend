from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.modules.audit_logs.model import AuditAction, AuditLog
from app.modules.audit_logs.service import AuditLogService
from app.modules.users.model import User
from app.shared.types import Role


def make_user(**kwargs) -> User:
    now = datetime.now(UTC)
    defaults = {
        "id": 1,
        "name": "Test User",
        "email": "test@test.com",
        "role": Role.USER,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    user = MagicMock(spec=User)
    for key, value in defaults.items():
        setattr(user, key, value)
    return user


def make_audit_log(**kwargs) -> AuditLog:
    now = datetime.now(UTC)
    defaults = {
        "id": 1,
        "action": AuditAction.USER_CREATED,
        "performed_by_id": 99,
        "performed_by_name": "Admin",
        "target_user_id": 1,
        "target_user_name": "Test User",
        "target_user_email": "test@test.com",
        "target_user_role": "USER",
        "target_client_id": None,
        "target_client_name": None,
        "created_at": now,
    }
    defaults.update(kwargs)
    log = MagicMock(spec=AuditLog)
    for key, value in defaults.items():
        setattr(log, key, value)
    return log


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    return AuditLogService(repo)


class TestLogUserCreated:
    def test_calls_repo_with_user_created_action(self, service, repo):
        user = make_user()
        admin = make_user(id=99, name="Admin")

        service.log_user_created(user, performed_by=admin)

        assert repo.create.call_args.kwargs["action"] == AuditAction.USER_CREATED

    def test_passes_correct_performed_by_id(self, service, repo):
        user = make_user()
        admin = make_user(id=42, name="Admin")

        service.log_user_created(user, performed_by=admin)

        assert repo.create.call_args.kwargs["performed_by_id"] == 42

    def test_passes_correct_performed_by_name(self, service, repo):
        user = make_user()
        admin = make_user(id=1, name="Super Admin")

        service.log_user_created(user, performed_by=admin)

        assert repo.create.call_args.kwargs["performed_by_name"] == "Super Admin"

    def test_captures_target_user_snapshot(self, service, repo):
        user = make_user(id=5, name="Bob", email="bob@test.com", role=Role.ADMIN)
        admin = make_user(id=1, name="Admin")

        service.log_user_created(user, performed_by=admin)

        kwargs = repo.create.call_args.kwargs
        assert kwargs["target_user_id"] == 5
        assert kwargs["target_user_name"] == "Bob"
        assert kwargs["target_user_email"] == "bob@test.com"
        assert kwargs["target_user_role"] == "ADMIN"

    def test_calls_repo_create_exactly_once(self, service, repo):
        service.log_user_created(
            make_user(), performed_by=make_user(id=1, name="Admin")
        )

        repo.create.assert_called_once()


class TestLogUserDeactivated:
    def test_calls_repo_with_user_deactivated_action(self, service, repo):
        user = make_user()
        admin = make_user(id=1, name="Admin")

        service.log_user_deactivated(user, performed_by=admin)

        assert repo.create.call_args.kwargs["action"] == AuditAction.USER_DEACTIVATED

    def test_passes_correct_performed_by_id(self, service, repo):
        user = make_user()
        admin = make_user(id=7, name="Admin")

        service.log_user_deactivated(user, performed_by=admin)

        assert repo.create.call_args.kwargs["performed_by_id"] == 7

    def test_passes_correct_performed_by_name(self, service, repo):
        user = make_user()
        admin = make_user(id=1, name="Super Admin")

        service.log_user_deactivated(user, performed_by=admin)

        assert repo.create.call_args.kwargs["performed_by_name"] == "Super Admin"

    def test_captures_target_user_snapshot(self, service, repo):
        user = make_user(id=3, name="Carol", email="carol@test.com", role=Role.USER)
        admin = make_user(id=1, name="Admin")

        service.log_user_deactivated(user, performed_by=admin)

        kwargs = repo.create.call_args.kwargs
        assert kwargs["target_user_id"] == 3
        assert kwargs["target_user_name"] == "Carol"
        assert kwargs["target_user_email"] == "carol@test.com"
        assert kwargs["target_user_role"] == "USER"

    def test_calls_repo_create_exactly_once(self, service, repo):
        service.log_user_deactivated(
            make_user(), performed_by=make_user(id=1, name="Admin")
        )

        repo.create.assert_called_once()


class TestLogUserUpdated:
    def test_calls_repo_with_user_updated_action(self, service, repo):
        user = make_user()
        admin = make_user(id=99, name="Admin")

        service.log_user_updated(user, performed_by=admin)

        assert repo.create.call_args.kwargs["action"] == AuditAction.USER_UPDATED

    def test_passes_correct_performed_by_id(self, service, repo):
        user = make_user()
        admin = make_user(id=42, name="Admin")

        service.log_user_updated(user, performed_by=admin)

        assert repo.create.call_args.kwargs["performed_by_id"] == 42

    def test_passes_correct_performed_by_name(self, service, repo):
        user = make_user()
        admin = make_user(id=1, name="Super Admin")

        service.log_user_updated(user, performed_by=admin)

        assert repo.create.call_args.kwargs["performed_by_name"] == "Super Admin"

    def test_captures_target_user_snapshot(self, service, repo):
        user = make_user(id=7, name="Dave", email="dave@test.com", role=Role.ADMIN)
        admin = make_user(id=1, name="Admin")

        service.log_user_updated(user, performed_by=admin)

        kwargs = repo.create.call_args.kwargs
        assert kwargs["target_user_id"] == 7
        assert kwargs["target_user_name"] == "Dave"
        assert kwargs["target_user_email"] == "dave@test.com"
        assert kwargs["target_user_role"] == "ADMIN"

    def test_calls_repo_create_exactly_once(self, service, repo):
        service.log_user_updated(
            make_user(), performed_by=make_user(id=1, name="Admin")
        )

        repo.create.assert_called_once()


class TestListLogs:
    def test_calls_repo_get_all_with_correct_params(self, service, repo):
        repo.get_all.return_value = ([], 0)

        service.list_logs(
            action=AuditAction.USER_CREATED,
            date_from=None,
            date_to=None,
            page=2,
            limit=10,
        )

        repo.get_all.assert_called_once_with(
            action=AuditAction.USER_CREATED,
            date_from=None,
            date_to=None,
            page=2,
            limit=10,
        )

    def test_returns_audit_log_read_list(self, service, repo):
        logs = [make_audit_log(id=1), make_audit_log(id=2)]
        repo.get_all.return_value = (logs, 2)

        result, total = service.list_logs(
            action=None, date_from=None, date_to=None, page=1, limit=20
        )

        assert len(result) == 2
        assert total == 2

    def test_returns_empty_list_when_no_logs(self, service, repo):
        repo.get_all.return_value = ([], 0)

        result, total = service.list_logs(
            action=None, date_from=None, date_to=None, page=1, limit=20
        )

        assert result == []
        assert total == 0

    def test_passes_none_filters_to_repo(self, service, repo):
        repo.get_all.return_value = ([], 0)

        service.list_logs(action=None, date_from=None, date_to=None, page=1, limit=20)

        repo.get_all.assert_called_once_with(
            action=None, date_from=None, date_to=None, page=1, limit=20
        )
