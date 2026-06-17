from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.orm import Session

from app.modules.leads.model import Lead, LeadStatus
from app.modules.leads.repository import LeadRepository
from app.modules.users.repository import UserRepository
from app.shared.types import Role


def make_lead(repo: LeadRepository, **kwargs) -> Lead:
    defaults = {
        "name": "João Silva",
        "email": "joao@example.com",
        "phone": None,
        "message": "Gostaria de uma consulta",
    }
    defaults.update(kwargs)
    return repo.create(**defaults)


class TestCreate:
    def test_persists_lead_with_correct_fields(self, db: Session):
        repo = LeadRepository(db)

        lead = make_lead(repo, name="Maria Souza", email="maria@example.com")

        assert lead.id is not None
        assert lead.name == "Maria Souza"
        assert lead.email == "maria@example.com"
        assert lead.status == LeadStatus.NOVO
        assert lead.assigned_to is None
        assert lead.created_at is not None

    def test_default_status_is_novo(self, db: Session):
        repo = LeadRepository(db)

        lead = make_lead(repo, email="status@example.com")

        assert lead.status == LeadStatus.NOVO


class TestGetById:
    def test_returns_lead_when_exists(self, db: Session):
        repo = LeadRepository(db)
        created = make_lead(repo, email="getbyid@example.com")

        found = repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_not_exists(self, db: Session):
        repo = LeadRepository(db)

        assert repo.get_by_id(99999) is None


class TestFindRecentByEmail:
    def test_returns_lead_created_within_window(self, db: Session):
        repo = LeadRepository(db)
        lead = make_lead(repo, email="recent@example.com")

        found = repo.find_recent_by_email("recent@example.com", window_hours=1)

        assert found is not None
        assert found.id == lead.id

    def test_returns_none_when_lead_outside_window(self, db: Session):
        repo = LeadRepository(db)
        lead = make_lead(repo, email="old@example.com")
        lead.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()

        found = repo.find_recent_by_email("old@example.com", window_hours=1)

        assert found is None

    def test_returns_none_when_email_not_found(self, db: Session):
        repo = LeadRepository(db)

        assert repo.find_recent_by_email("noemail@example.com", window_hours=1) is None


class TestGetAll:
    def test_returns_all_leads_paginated(self, db: Session):
        repo = LeadRepository(db)
        make_lead(repo, email="a1@example.com")
        make_lead(repo, email="a2@example.com")

        leads, total = repo.get_all(page=1, limit=10)

        assert total >= 2
        assert len(leads) >= 2

    def test_filters_by_status(self, db: Session):
        repo = LeadRepository(db)
        lead = make_lead(repo, email="filter_status@example.com")
        repo.update(lead, {"status": LeadStatus.FECHADO})

        leads, total = repo.get_all(status=LeadStatus.FECHADO)

        assert all(lead.status == LeadStatus.FECHADO for lead in leads)

    def test_pagination_limits_results(self, db: Session):
        repo = LeadRepository(db)
        make_lead(repo, email="p1@example.com")
        make_lead(repo, email="p2@example.com")
        make_lead(repo, email="p3@example.com")

        leads, total = repo.get_all(page=1, limit=2)

        assert len(leads) <= 2
        assert total >= 3


class TestUpdate:
    def test_updates_status(self, db: Session):
        repo = LeadRepository(db)
        lead = make_lead(repo, email="update@example.com")

        updated = repo.update(lead, {"status": LeadStatus.EM_ATENDIMENTO})

        assert updated.status == LeadStatus.EM_ATENDIMENTO

    def test_assigns_responsible(self, db: Session):
        user = UserRepository(db).create(
            name="Advogado",
            email="adv_lead_test@example.com",
            hashed_password=bcrypt.hashpw(b"pass", bcrypt.gensalt()).decode(),
            role=Role.USER,
        )
        repo = LeadRepository(db)
        lead = make_lead(repo, email="assign@example.com")

        updated = repo.update(lead, {"assigned_to": user.id})

        assert updated.assigned_to == user.id
