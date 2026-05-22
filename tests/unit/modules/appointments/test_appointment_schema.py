from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.modules.appointments.model import AppointmentType
from app.modules.appointments.schema import AppointmentCreate, AppointmentUpdate

PAST = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
FUTURE = datetime.now(timezone.utc) + timedelta(days=30)


class TestAppointmentCreate:
    def test_accepts_future_starts_at(self):
        appt = AppointmentCreate(
            title="Audiência",
            type=AppointmentType.AUDIENCIA,
            starts_at=FUTURE,
            duration_minutes=60,
        )
        assert appt.duration_minutes == 60

    def test_rejects_past_starts_at(self):
        with pytest.raises(ValidationError):
            AppointmentCreate(
                title="x",
                type=AppointmentType.REUNIAO,
                starts_at=PAST,
                duration_minutes=30,
            )

    def test_rejects_non_positive_duration(self):
        with pytest.raises(ValidationError):
            AppointmentCreate(
                title="x",
                type=AppointmentType.OUTRO,
                starts_at=FUTURE,
                duration_minutes=0,
            )

    def test_rejects_blank_title(self):
        with pytest.raises(ValidationError):
            AppointmentCreate(
                title="",
                type=AppointmentType.OUTRO,
                starts_at=FUTURE,
                duration_minutes=30,
            )


class TestAppointmentUpdate:
    def test_allows_past_starts_at(self):
        upd = AppointmentUpdate(starts_at=PAST)
        assert upd.starts_at == PAST

    def test_forbids_unknown_field(self):
        with pytest.raises(ValidationError):
            AppointmentUpdate(unknown="value")
