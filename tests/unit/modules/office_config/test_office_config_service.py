from unittest.mock import MagicMock

import pytest

from app.modules.office_config.model import OfficeConfig
from app.modules.office_config.schema import (
    ListItem,
    OfficeConfigRead,
    OfficeConfigUpdate,
)
from app.modules.office_config.service import OfficeConfigService


def make_config(**kwargs) -> OfficeConfig:
    defaults = {
        "id": 1,
        "office_name": None,
        "cnpj": None,
        "address": None,
        "phone": None,
        "email": None,
        "instagram_url": None,
        "linkedin_url": None,
        "whatsapp_url": None,
        "hero_title": None,
        "hero_subtitle": None,
        "hero_image_url": None,
        "about_title": None,
        "about_description": None,
        "about_image_url": None,
        "lawyer_name": None,
        "lawyer_oab": None,
        "lawyer_description": None,
        "lawyer_image_url": None,
        "differentials": [],
        "areas_of_practice": [],
    }
    defaults.update(kwargs)
    config = MagicMock(spec=OfficeConfig)
    for key, value in defaults.items():
        setattr(config, key, value)
    return config


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    svc = OfficeConfigService.__new__(OfficeConfigService)
    svc.repository = repo
    return svc


class TestGet:
    def test_returns_office_config_read(self, service, repo):
        repo.get_config.return_value = make_config()
        result = service.get()
        assert isinstance(result, OfficeConfigRead)

    def test_maps_fields_correctly(self, service, repo):
        repo.get_config.return_value = make_config(
            office_name="Escritório X", cnpj="00.000.000/0001-00"
        )
        result = service.get()
        assert result.office_name == "Escritório X"
        assert result.cnpj == "00.000.000/0001-00"

    def test_none_list_fields_become_empty_list(self, service, repo):
        repo.get_config.return_value = make_config(
            differentials=None, areas_of_practice=None
        )
        result = service.get()
        assert result.differentials == []
        assert result.areas_of_practice == []


class TestUpdate:
    def test_calls_repository_with_non_none_fields_only(self, service, repo):
        repo.update_config.return_value = make_config(office_name="Novo")
        service.update(OfficeConfigUpdate(office_name="Novo"))
        repo.update_config.assert_called_once_with({"office_name": "Novo"})

    def test_excludes_none_fields_from_update(self, service, repo):
        repo.update_config.return_value = make_config()
        service.update(OfficeConfigUpdate(office_name=None, hero_title=None))
        repo.update_config.assert_called_once_with({})

    def test_serializes_differentials_to_dicts(self, service, repo):
        repo.update_config.return_value = make_config(
            differentials=[{"title": "T", "description": "D"}]
        )
        service.update(
            OfficeConfigUpdate(differentials=[ListItem(title="T", description="D")])
        )
        call_data = repo.update_config.call_args[0][0]
        assert call_data["differentials"] == [{"title": "T", "description": "D"}]

    def test_serializes_areas_of_practice_to_dicts(self, service, repo):
        repo.update_config.return_value = make_config(
            areas_of_practice=[{"title": "A", "description": "B"}]
        )
        service.update(
            OfficeConfigUpdate(areas_of_practice=[ListItem(title="A", description="B")])
        )
        call_data = repo.update_config.call_args[0][0]
        assert call_data["areas_of_practice"] == [{"title": "A", "description": "B"}]

    def test_returns_office_config_read(self, service, repo):
        repo.update_config.return_value = make_config(office_name="X")
        result = service.update(OfficeConfigUpdate(office_name="X"))
        assert isinstance(result, OfficeConfigRead)
        assert result.office_name == "X"
