import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-enough-length")
os.environ.setdefault("RESEND_API_KEY", "re_test")

from app.modules.clients.repository import ClientRepository
from app.modules.datajud.fake_service import FakeDataJudService
from app.modules.datajud.schema import DataJudMovement
from app.modules.external_api_logs.model import ExternalApiLog  # noqa: F401
from app.modules.notifications.model import NotificationPreference  # noqa: F401
from app.modules.processes.repository import ProcessRepository
from app.modules.users.repository import UserRepository
from app.shared.base_model import Base
from app.shared.types import Role
from scripts.sync_datajud_active_processes import (
    build_parser,
    resolve_sync_user_id,
    run_sync,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def test_parser_reads_defaults(monkeypatch):
    monkeypatch.setenv("DATAJUD_SYNC_TRIBUNAL_ALIAS", "tjsp")
    monkeypatch.setenv("DATAJUD_SYNC_LIMIT", "25")
    monkeypatch.setenv("DATAJUD_SYNC_USER_ID", "7")

    args = build_parser().parse_args([])

    assert args.tribunal_alias == "tjsp"
    assert args.limit == 25
    assert args.user_id == 7


def test_resolve_sync_user_id_validates_existing_user(db):
    user = UserRepository(db).create(
        name="Admin",
        email="admin_sync@test.com",
        hashed_password="hash",
        role=Role.ADMIN,
    )

    assert resolve_sync_user_id(db, user.id) == user.id
    with pytest.raises(ValueError):
        resolve_sync_user_id(db, user.id + 1)


def test_run_sync_uses_saved_tribunal_alias(db):
    client = ClientRepository(db).create(name="Cliente Script", cpf="11122233355")
    ProcessRepository(db).create(
        number="12345678920248262100",
        client_id=client.id,
        court="TJSP",
        tribunal_alias="tjsp",
        action_type="Ação Cível",
    )
    fake = FakeDataJudService(
        movements=[
            DataJudMovement(
                external_id="script-mov-1",
                title="Movimento script",
                occurred_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )
        ]
    )

    result = run_sync(
        tribunal_alias=None,
        limit=10,
        db=db,
        datajud_client=fake,
    )

    assert result.success_count == 1
    assert result.imported_count == 1
    assert fake.calls == [("12345678920248262100", "tjsp")]
