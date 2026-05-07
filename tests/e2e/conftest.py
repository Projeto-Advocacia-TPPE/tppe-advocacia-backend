import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.main import app
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository


@pytest.fixture(scope="session", autouse=True)
def require_database():
    settings = get_settings()
    try:
        engine = create_engine(
            settings.database_url,
            connect_args={"connect_timeout": 3},
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
    except Exception:
        pytest.skip("PostgreSQL unavailable — run: docker-compose up -d")


@pytest.fixture(scope="session")
def db_engine():
    from app.db.database import engine
    return engine


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture
def active_user(db_session):
    password = "Valid@1234"
    user = UserRepository(db_session).create(
        name="Active User",
        email="e2e_active@test.com",
        hashed_password=_hash(password),
        role=Role.USER,
    )
    yield {"id": user.id, "email": user.email, "password": password}
    db_session.execute(delete(User).where(User.id == user.id))
    db_session.commit()


@pytest.fixture
def inactive_user(db_session):
    password = "Valid@1234"
    repo = UserRepository(db_session)
    user = repo.create(
        name="Inactive User",
        email="e2e_inactive@test.com",
        hashed_password=_hash(password),
        role=Role.USER,
    )
    repo.update(user, {"is_active": False})
    yield {"id": user.id, "email": user.email, "password": password}
    db_session.execute(delete(User).where(User.id == user.id))
    db_session.commit()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
