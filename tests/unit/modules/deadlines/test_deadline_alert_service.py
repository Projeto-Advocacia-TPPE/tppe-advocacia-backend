from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.modules.deadlines.service import (
    EXPIRED_DAYS_BEFORE,
    DeadlineService,
    _smallest_interval,
)
from app.modules.notifications.schema import EventType

INTERVALS = [30, 15, 7, 3, 2, 1]
TODAY = date(2026, 5, 11)  # segunda-feira


def make_deadline(
    *,
    id: int = 1,
    due_date: date,
    created_by: int | None = 3,
    court: str | None = None,
    comarca: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        process_id=1,
        due_date=due_date,
        created_by=created_by,
        court=court,
        comarca=comarca,
        deadline_type="Contestação",
    )


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def holidays():
    m = MagicMock()
    m.list_applicable_in_range.return_value = []
    return m


@pytest.fixture
def processes():
    m = MagicMock()
    m.get_by_id.return_value = SimpleNamespace(number="99999999999999999991")
    return m


@pytest.fixture
def alerts():
    m = MagicMock()
    m.sent_days_for.return_value = set()
    return m


@pytest.fixture
def notifications():
    return MagicMock()


@pytest.fixture
def service(repo, holidays, processes, alerts, notifications):
    return DeadlineService(
        repository=repo,
        holiday_repository=holidays,
        process_repository=processes,
        alert_repository=alerts,
        notification_service=notifications,
        alert_intervals=INTERVALS,
    )


class TestSmallestInterval:
    def test_exact_match(self):
        assert _smallest_interval(INTERVALS, 7) == 7

    def test_picks_smallest_applicable_for_retroactive(self):
        # criado faltando 5 dias úteis → menor janela aplicável é 7
        assert _smallest_interval(INTERVALS, 5) == 7

    def test_none_when_beyond_largest(self):
        assert _smallest_interval(INTERVALS, 45) is None


class TestBusinessDaysUntil:
    def test_counts_business_days(self, service):
        # (11/05, 18/05]: ter-sex = 4, fim de semana pulado, seg 18 = 1 → 5
        assert service.business_days_until(date(2026, 5, 18), TODAY, None, None) == 5

    def test_zero_when_due_in_past(self, service):
        assert service.business_days_until(date(2026, 5, 8), TODAY, None, None) == 0

    def test_skips_holiday(self, service, holidays):
        holidays.list_applicable_in_range.return_value = [
            SimpleNamespace(date=date(2026, 5, 12), description="Feriado")
        ]
        # 12/05 vira feriado → 18/05 deixa de ter 5 dias úteis e passa a 4
        assert service.business_days_until(date(2026, 5, 18), TODAY, None, None) == 4


class TestDispatchAlerts:
    def test_fires_approaching_on_exact_interval(
        self, service, repo, alerts, notifications
    ):
        # 20/05: (11,20] = ter-sex(4) + seg-qua(3) = 7 dias úteis
        repo.list_all.return_value = [make_deadline(due_date=date(2026, 5, 20))]

        sent = service.dispatch_alerts(today=TODAY)

        assert sent == 1
        notifications.notify.assert_called_once()
        args = notifications.notify.call_args
        assert args.args[0] == 3  # created_by
        assert args.args[1] == EventType.DEADLINE_APPROACHING
        alerts.create.assert_called_once_with(1, 7)

    def test_retroactive_fires_smallest_window(self, service, repo, alerts):
        # 18/05: 5 dias úteis → menor janela aplicável é 7
        repo.list_all.return_value = [make_deadline(due_date=date(2026, 5, 18))]

        service.dispatch_alerts(today=TODAY)

        alerts.create.assert_called_once_with(1, 7)

    def test_does_not_duplicate_already_sent(self, service, repo, alerts):
        repo.list_all.return_value = [make_deadline(due_date=date(2026, 5, 20))]
        alerts.sent_days_for.return_value = {7}

        sent = service.dispatch_alerts(today=TODAY)

        assert sent == 0
        alerts.create.assert_not_called()

    def test_fires_expired_once(self, service, repo, alerts, notifications):
        repo.list_all.return_value = [make_deadline(due_date=date(2026, 5, 8))]

        sent = service.dispatch_alerts(today=TODAY)

        assert sent == 1
        assert notifications.notify.call_args.args[1] == EventType.DEADLINE_EXPIRED
        alerts.create.assert_called_once_with(1, EXPIRED_DAYS_BEFORE)

    def test_expired_not_duplicated(self, service, repo, alerts):
        repo.list_all.return_value = [make_deadline(due_date=date(2026, 5, 8))]
        alerts.sent_days_for.return_value = {EXPIRED_DAYS_BEFORE}

        assert service.dispatch_alerts(today=TODAY) == 0

    def test_skips_deadline_without_created_by(self, service, repo, notifications):
        repo.list_all.return_value = [
            make_deadline(due_date=date(2026, 5, 20), created_by=None)
        ]

        assert service.dispatch_alerts(today=TODAY) == 0
        notifications.notify.assert_not_called()

    def test_no_alert_when_beyond_largest_interval(self, service, repo, alerts):
        # due_date muito distante → nenhum intervalo aplicável
        repo.list_all.return_value = [make_deadline(due_date=date(2026, 9, 1))]

        assert service.dispatch_alerts(today=TODAY) == 0
        alerts.create.assert_not_called()
