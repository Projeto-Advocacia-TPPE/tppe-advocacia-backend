from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.audit_logs.model import AuditAction
from app.modules.audit_logs.repository import AuditLogRepository


def make_log(
    repo: AuditLogRepository,
    *,
    action: AuditAction = AuditAction.USER_CREATED,
    performed_by_id: int | None = 1,
    performed_by_name: str | None = "Admin User",
    target_user_id: int = 10,
    target_user_name: str = "Test User",
    target_user_email: str = "test@test.com",
    target_user_role: str = "USER",
):
    return repo.create(
        action=action,
        performed_by_id=performed_by_id,
        performed_by_name=performed_by_name,
        target_user_id=target_user_id,
        target_user_name=target_user_name,
        target_user_email=target_user_email,
        target_user_role=target_user_role,
    )


class TestCreate:
    def test_creates_log_with_correct_action(self, db: Session):
        repo = AuditLogRepository(db)
        log = make_log(repo, action=AuditAction.USER_CREATED)

        assert log.action == AuditAction.USER_CREATED

    def test_creates_log_with_deactivated_action(self, db: Session):
        repo = AuditLogRepository(db)
        log = make_log(repo, action=AuditAction.USER_DEACTIVATED)

        assert log.action == AuditAction.USER_DEACTIVATED

    def test_assigns_id(self, db: Session):
        repo = AuditLogRepository(db)
        log = make_log(repo)

        assert log.id is not None

    def test_stores_performed_by_id(self, db: Session):
        repo = AuditLogRepository(db)
        log = make_log(repo, performed_by_id=42)

        assert log.performed_by_id == 42

    def test_accepts_null_performed_by_id(self, db: Session):
        repo = AuditLogRepository(db)
        log = make_log(repo, performed_by_id=None, performed_by_name=None)

        assert log.performed_by_id is None

    def test_stores_performed_by_name(self, db: Session):
        repo = AuditLogRepository(db)
        log = make_log(repo, performed_by_name="Super Admin")

        assert log.performed_by_name == "Super Admin"

    def test_accepts_null_performed_by_name(self, db: Session):
        repo = AuditLogRepository(db)
        log = make_log(repo, performed_by_name=None)

        assert log.performed_by_name is None

    def test_stores_target_user_snapshot(self, db: Session):
        repo = AuditLogRepository(db)
        log = make_log(
            repo,
            target_user_id=99,
            target_user_name="Alice",
            target_user_email="alice@test.com",
            target_user_role="ADMIN",
        )

        assert log.target_user_id == 99
        assert log.target_user_name == "Alice"
        assert log.target_user_email == "alice@test.com"
        assert log.target_user_role == "ADMIN"

    def test_sets_created_at_automatically(self, db: Session):
        before = datetime.now(UTC).replace(microsecond=0, tzinfo=None)
        repo = AuditLogRepository(db)
        log = make_log(repo)

        assert log.created_at is not None
        assert log.created_at >= before


class TestGetAll:
    def test_returns_all_logs(self, db: Session):
        repo = AuditLogRepository(db)
        make_log(repo, target_user_id=1)
        make_log(repo, target_user_id=2)

        logs, total = repo.get_all()

        assert total == 2
        assert len(logs) == 2

    def test_returns_empty_when_no_logs(self, db: Session):
        repo = AuditLogRepository(db)

        logs, total = repo.get_all()

        assert total == 0
        assert logs == []

    def test_filters_by_action_created(self, db: Session):
        repo = AuditLogRepository(db)
        make_log(repo, action=AuditAction.USER_CREATED, target_user_id=1)
        make_log(repo, action=AuditAction.USER_DEACTIVATED, target_user_id=2)

        logs, total = repo.get_all(action=AuditAction.USER_CREATED)

        assert total == 1
        assert logs[0].action == AuditAction.USER_CREATED

    def test_filters_by_action_deactivated(self, db: Session):
        repo = AuditLogRepository(db)
        make_log(repo, action=AuditAction.USER_CREATED, target_user_id=1)
        make_log(repo, action=AuditAction.USER_DEACTIVATED, target_user_id=2)

        logs, total = repo.get_all(action=AuditAction.USER_DEACTIVATED)

        assert total == 1
        assert logs[0].action == AuditAction.USER_DEACTIVATED

    def test_date_from_excludes_logs_created_before_cutoff(self, db: Session):
        repo = AuditLogRepository(db)
        make_log(repo, target_user_id=1)

        future = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)
        logs, total = repo.get_all(date_from=future)

        assert total == 0

    def test_date_from_includes_logs_created_after_cutoff(self, db: Session):
        repo = AuditLogRepository(db)
        make_log(repo, target_user_id=1)

        past = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
        logs, total = repo.get_all(date_from=past)

        assert total == 1

    def test_date_to_excludes_logs_created_after_cutoff(self, db: Session):
        repo = AuditLogRepository(db)
        make_log(repo, target_user_id=1)

        past = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
        logs, total = repo.get_all(date_to=past)

        assert total == 0

    def test_date_to_includes_logs_created_before_cutoff(self, db: Session):
        repo = AuditLogRepository(db)
        make_log(repo, target_user_id=1)

        future = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)
        logs, total = repo.get_all(date_to=future)

        assert total == 1

    def test_pagination_respects_limit(self, db: Session):
        repo = AuditLogRepository(db)
        for i in range(5):
            make_log(repo, target_user_id=i)

        logs, total = repo.get_all(page=1, limit=2)

        assert total == 5
        assert len(logs) == 2

    def test_pagination_second_page_has_different_records(self, db: Session):
        repo = AuditLogRepository(db)
        for i in range(5):
            make_log(repo, target_user_id=i)

        logs_p1, _ = repo.get_all(page=1, limit=3)
        logs_p2, _ = repo.get_all(page=2, limit=3)

        ids_p1 = {log.id for log in logs_p1}
        ids_p2 = {log.id for log in logs_p2}
        assert ids_p1.isdisjoint(ids_p2)

    def test_results_ordered_by_created_at_desc(self, db: Session):
        repo = AuditLogRepository(db)
        for i in range(3):
            make_log(repo, target_user_id=i)

        logs, _ = repo.get_all()

        dates = [log.created_at for log in logs]
        assert dates == sorted(dates, reverse=True)

    def test_no_filter_returns_all_actions(self, db: Session):
        repo = AuditLogRepository(db)
        make_log(repo, action=AuditAction.USER_CREATED, target_user_id=1)
        make_log(repo, action=AuditAction.USER_DEACTIVATED, target_user_id=2)

        logs, total = repo.get_all()

        assert total == 2
        actions = {log.action for log in logs}
        assert AuditAction.USER_CREATED in actions
        assert AuditAction.USER_DEACTIVATED in actions
