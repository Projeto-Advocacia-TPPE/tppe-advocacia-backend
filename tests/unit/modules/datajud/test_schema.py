import pytest
from pydantic import ValidationError

from app.modules.datajud.schema import DataJudSyncRequest
from app.modules.processes.schema import ProcessCreate


class TestDataJudTribunalAlias:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("TJSP", "tjsp"),
            (" tjsp ", "tjsp"),
            ("trf-1", "trf-1"),
        ],
    )
    def test_normalizes_alias(self, raw, expected):
        assert DataJudSyncRequest(tribunal_alias=raw).tribunal_alias == expected

    @pytest.mark.parametrize("raw", ["", "t", "tj sp", "tj_sp", "a" * 31])
    def test_rejects_invalid_alias(self, raw):
        with pytest.raises(ValidationError):
            DataJudSyncRequest(tribunal_alias=raw)

    def test_process_create_accepts_datajud_alias(self):
        payload = ProcessCreate(
            number="1234567-89.2024.8.26.0100",
            court="TJSP",
            tribunal_alias="TJSP",
            action_type="Ação Cível",
        )

        assert payload.tribunal_alias == "tjsp"
