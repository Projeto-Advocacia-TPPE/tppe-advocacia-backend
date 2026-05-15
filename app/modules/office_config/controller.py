from sqlalchemy.orm import Session

from app.modules.office_config.repository import OfficeConfigRepository
from app.modules.office_config.schema import OfficeConfigRead, OfficeConfigUpdate
from app.modules.office_config.service import OfficeConfigService


class OfficeConfigController:
    def __init__(self, db: Session) -> None:
        self.service = OfficeConfigService(OfficeConfigRepository(db))

    def get(self) -> OfficeConfigRead:
        return self.service.get()

    def update(self, payload: OfficeConfigUpdate) -> OfficeConfigRead:
        return self.service.update(payload)
