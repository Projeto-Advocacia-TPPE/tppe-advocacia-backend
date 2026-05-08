import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.base import Base


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
