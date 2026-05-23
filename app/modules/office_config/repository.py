from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.office_config.model import OfficeConfig


class OfficeConfigRepository:
    """Este repositório nunca comita. Operações de escrita usam db.add + db.flush
    e o Service que orquestra a transação fecha com unit_of_work."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_config(self) -> OfficeConfig:
        return self.db.scalars(select(OfficeConfig).where(OfficeConfig.id == 1)).one()

    def update_config(self, data: dict) -> OfficeConfig:
        config = self.get_config()
        for key, value in data.items():
            setattr(config, key, value)
        self.db.flush()
        return config
