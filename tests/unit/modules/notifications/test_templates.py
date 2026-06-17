from app.modules.notifications.schema import EventType
from app.modules.notifications.templates import TEMPLATES


class TestTemplatesRegistry:
    def test_all_event_types_have_a_template(self):
        for event in EventType:
            assert event in TEMPLATES


class TestProcessMovementCreated:
    def test_renders_subject_and_body(self):
        subject, html = TEMPLATES[EventType.PROCESS_MOVEMENT_CREATED](
            {
                "process_number": "1234567-89.2024.8.26.0100",
                "title": "Petição inicial protocolada",
                "description": "Detalhes",
                "occurred_at": "2026-05-15T09:00:00Z",
            }
        )
        assert "1234567-89.2024.8.26.0100" in subject
        assert "Petição inicial protocolada" in html
        assert "Detalhes" in html

    def test_renders_without_description(self):
        subject, html = TEMPLATES[EventType.PROCESS_MOVEMENT_CREATED](
            {
                "process_number": "X",
                "title": "T",
                "description": None,
                "occurred_at": "2026-05-15T09:00:00Z",
            }
        )
        assert "T" in html


class TestProcessStatusChanged:
    def test_renders_with_reason(self):
        subject, html = TEMPLATES[EventType.PROCESS_STATUS_CHANGED](
            {
                "process_number": "X",
                "previous_status": "ATIVO",
                "new_status": "SUSPENSO",
                "reason": "Aguardando",
            }
        )
        assert "X" in subject
        assert "ATIVO" in html
        assert "SUSPENSO" in html
        assert "Aguardando" in html

    def test_renders_without_reason(self):
        _, html = TEMPLATES[EventType.PROCESS_STATUS_CHANGED](
            {
                "process_number": "X",
                "previous_status": "ATIVO",
                "new_status": "ENCERRADO",
                "reason": None,
            }
        )
        assert "Motivo" not in html


class TestLeadAssigned:
    def test_renders(self):
        subject, html = TEMPLATES[EventType.LEAD_ASSIGNED](
            {
                "lead_id": 7,
                "lead_name": "João Silva",
                "lead_email": "joao@test.com",
                "lead_phone": "11999999999",
            }
        )
        assert "7" in subject
        assert "João Silva" in subject
        assert "joao@test.com" in html
        assert "11999999999" in html


class TestTaskAssigned:
    def test_renders_with_due_date(self):
        subject, html = TEMPLATES[EventType.TASK_ASSIGNED](
            {
                "task_id": 3,
                "task_title": "Revisar contrato",
                "due_date": "2026-06-01",
            }
        )
        assert "Revisar contrato" in subject
        assert "2026-06-01" in html

    def test_renders_without_due_date(self):
        _, html = TEMPLATES[EventType.TASK_ASSIGNED](
            {"task_id": 1, "task_title": "T", "due_date": None}
        )
        assert "Prazo" not in html
