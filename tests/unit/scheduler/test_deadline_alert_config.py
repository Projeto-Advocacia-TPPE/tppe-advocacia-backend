import pytest

from app.config.settings import Settings


def make_settings(**overrides) -> Settings:
    base = {"JWT_SECRET_KEY": "x" * 32, "RESEND_API_KEY": "re_test"}
    base.update(overrides)
    return Settings(**base)


class TestCronParts:
    def test_default_is_six_am(self):
        assert make_settings().deadline_alert_cron_parts == (6, 0)

    def test_parses_custom_time(self):
        assert make_settings(DEADLINE_ALERT_CRON="07:30").deadline_alert_cron_parts == (
            7,
            30,
        )

    def test_rejects_malformed_value(self):
        with pytest.raises(ValueError):
            make_settings(DEADLINE_ALERT_CRON="6h30").deadline_alert_cron_parts

    def test_rejects_out_of_range_hour(self):
        with pytest.raises(ValueError):
            make_settings(DEADLINE_ALERT_CRON="25:00").deadline_alert_cron_parts


class TestAlertIntervals:
    def test_default_intervals(self):
        assert make_settings().deadline_alert_intervals == [30, 15, 7, 3, 2, 1]

    def test_parses_comma_separated_string(self):
        assert make_settings(
            DEADLINE_ALERT_INTERVALS="10,5,1"
        ).deadline_alert_intervals == [10, 5, 1]

    def test_ignores_blank_segments(self):
        assert make_settings(
            DEADLINE_ALERT_INTERVALS="30, 15 , 7,"
        ).deadline_alert_intervals == [30, 15, 7]
