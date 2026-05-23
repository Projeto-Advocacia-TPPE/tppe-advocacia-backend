from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.forensic_holidays.repository import ForensicHolidayRepository
from app.modules.forensic_holidays.service import ForensicHolidayService


def get_forensic_holiday_service(db: Session = Depends(get_db)) -> ForensicHolidayService:
    return ForensicHolidayService(ForensicHolidayRepository(db))
