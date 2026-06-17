from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.modules.clients.repository import ClientRepository
from app.modules.clients.timeline_repository import TimelineRepository
from app.modules.clients.timeline_service import ClientTimelineService
from app.modules.processes.model import MovementSource
from app.modules.processes.repository import ProcessRepository
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.shared.types import Role


@pytest.fixture
def author(db: Session) -> User:
    return UserRepository(db).create(
        name="Q Counter",
        email="qc@test.com",
        hashed_password="x",
        role=Role.USER,
    )


@pytest.fixture
def populated_client(db: Session, author):
    crepo = ClientRepository(db)
    prepo = ProcessRepository(db)
    client = crepo.create(name="Cli QC", cpf="55566677700")

    for i in range(2):
        crepo.create_note(client_id=client.id, created_by=author.id, content=f"n{i}")

    base = datetime.now(timezone.utc) - timedelta(days=10)
    for i in range(3):
        p = prepo.create(
            number=f"1234567892024826990{i}",
            client_id=client.id,
            court="TJSP",
            action_type="A",
        )
        for j in range(2):
            prepo.create_movement(
                process_id=p.id,
                title=f"m{i}-{j}",
                occurred_at=base + timedelta(days=j),
                source=MovementSource.MANUAL,
                created_by=author.id,
            )

    return client


class TestTimelineQueryBudget:
    def test_full_timeline_uses_at_most_4_selects(self, db: Session, populated_client):
        client_id = populated_client.id
        select_count = 0

        seen_statements: list[str] = []

        def before_cursor(conn, cursor, statement, parameters, context, executemany):
            nonlocal select_count
            stripped = statement.strip().upper()
            if stripped.startswith("SELECT") or stripped.startswith("WITH"):
                select_count += 1
                seen_statements.append(statement.strip()[:120])

        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", before_cursor)
        try:
            service = ClientTimelineService(
                ClientRepository(db),
                ProcessRepository(db),
                TimelineRepository(db),
            )
            timeline = service.get_timeline(client_id)

            assert len(timeline.processes) == 3
            assert len(timeline.notes) == 2
            assert len(timeline.recent_activity) > 0
        finally:
            event.remove(engine, "before_cursor_execute", before_cursor)

        assert select_count <= 4, (
            f"Timeline fetch used {select_count} SELECT queries (budget is 4)\n"
            + "\n".join(f"  - {s}" for s in seen_statements)
        )
