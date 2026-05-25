from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.office_config.repository import OfficeConfigRepository
from app.modules.office_config.service import OfficeConfigService


def get_office_config_service(db: Session = Depends(get_db)) -> OfficeConfigService:
    return OfficeConfigService(OfficeConfigRepository(db))
