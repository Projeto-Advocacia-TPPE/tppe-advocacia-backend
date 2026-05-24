from app.modules.office_config.model import OfficeConfig
from app.modules.office_config.repository import OfficeConfigRepository
from app.modules.office_config.schema import OfficeConfigUpdate
from app.shared.uow import unit_of_work


class OfficeConfigService:
    def __init__(self, repository: OfficeConfigRepository) -> None:
        self.repository = repository

    def get(self) -> OfficeConfig:
        return self.repository.get_config()

    def update(self, payload: OfficeConfigUpdate) -> OfficeConfig:
        data = payload.model_dump(exclude_unset=True)
        with unit_of_work(self.repository.db):
            return self.repository.update_config(data)
