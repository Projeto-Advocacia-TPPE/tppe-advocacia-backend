from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings
from app.shared.base_model import Base

settings = get_settings()

engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    from app.modules.articles.model import Article  # noqa: F401
    from app.modules.audit_logs.model import AuditLog  # noqa: F401
    from app.modules.clients.model import Client  # noqa: F401
    from app.modules.leads.model import Lead  # noqa: F401
    from app.modules.office_config.model import OfficeConfig  # noqa: F401
    from app.modules.users.model import User  # noqa: F401

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        from sqlalchemy import select

        existing = db.scalars(select(OfficeConfig).where(OfficeConfig.id == 1)).first()
        if existing is None:
            db.add(OfficeConfig(id=1, differentials=[], areas_of_practice=[]))
            db.commit()


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
