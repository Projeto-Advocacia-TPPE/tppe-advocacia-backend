import pytest
from pydantic import ValidationError

from app.modules.processes.schema import ProcessCreate, normalize_cnj


class TestNormalizeCnj:
    def test_returns_masked_when_already_masked(self):
        assert normalize_cnj("1234567-89.2024.8.26.0100") == "1234567-89.2024.8.26.0100"

    def test_normalizes_digits_only_to_masked(self):
        assert normalize_cnj("12345678920248260100") == "1234567-89.2024.8.26.0100"

    def test_strips_non_digit_and_masks(self):
        assert normalize_cnj("1234567 89 2024 8 26 0100") == "1234567-89.2024.8.26.0100"

    def test_raises_on_short_input(self):
        with pytest.raises(ValueError):
            normalize_cnj("123")

    def test_raises_on_long_input(self):
        with pytest.raises(ValueError):
            normalize_cnj("123456789012345678901")

    def test_raises_on_non_string(self):
        with pytest.raises(ValueError):
            normalize_cnj(12345678920248260100)  # type: ignore[arg-type]


class TestProcessCreateSchema:
    def test_accepts_masked_number(self):
        payload = ProcessCreate(
            number="1234567-89.2024.8.26.0100",
            client_id=1,
            court="TJSP",
            action_type="Ação Cível",
        )
        assert payload.number == "1234567-89.2024.8.26.0100"

    def test_normalizes_digits_only_number(self):
        payload = ProcessCreate(
            number="12345678920248260100",
            client_id=1,
            court="TJSP",
            action_type="Ação Cível",
        )
        assert payload.number == "1234567-89.2024.8.26.0100"

    def test_rejects_invalid_number(self):
        with pytest.raises(ValidationError):
            ProcessCreate(
                number="abc",
                client_id=1,
                court="TJSP",
                action_type="Ação Cível",
            )

    def test_rejects_invalid_client_id(self):
        with pytest.raises(ValidationError):
            ProcessCreate(
                number="1234567-89.2024.8.26.0100",
                client_id=0,
                court="TJSP",
                action_type="Ação Cível",
            )

    def test_accepts_without_client_id(self):
        payload = ProcessCreate(
            number="1234567-89.2024.8.26.0100",
            court="TJSP",
            action_type="Ação Cível",
        )
        assert payload.client_id is None
