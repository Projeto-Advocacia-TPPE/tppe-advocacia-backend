import pytest
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import get_settings


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


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
