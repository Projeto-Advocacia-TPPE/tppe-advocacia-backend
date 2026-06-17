from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.audit_logs.service import AuditLogService
from app.modules.clients.repository import ClientRepository
from app.modules.clients.service import ClientService
from app.modules.clients.timeline_repository import TimelineRepository
from app.modules.clients.timeline_service import ClientTimelineService
from app.modules.processes.repository import ProcessRepository


def get_client_service(db: Session = Depends(get_db)) -> ClientService:
    return ClientService(
        ClientRepository(db),
        process_repository=ProcessRepository(db),
        audit=AuditLogService(AuditLogRepository(db)),
    )


def get_client_timeline_service(db: Session = Depends(get_db)) -> ClientTimelineService:
    return ClientTimelineService(
        ClientRepository(db),
        ProcessRepository(db),
        TimelineRepository(db),
    )
