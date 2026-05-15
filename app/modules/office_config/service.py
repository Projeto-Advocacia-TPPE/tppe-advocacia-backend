from app.modules.office_config.repository import OfficeConfigRepository
from app.modules.office_config.schema import OfficeConfigRead, OfficeConfigUpdate


class OfficeConfigService:
    def __init__(self, repository: OfficeConfigRepository) -> None:
        self.repository = repository

    def get(self) -> OfficeConfigRead:
        config = self.repository.get_config()
        return OfficeConfigRead.model_validate(config)

    def update(self, payload: OfficeConfigUpdate) -> OfficeConfigRead:
        data = payload.model_dump(exclude_none=True)
        config = self.repository.update_config(data)
        return OfficeConfigRead.model_validate(config)
