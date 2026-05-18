from __future__ import annotations

from sqlalchemy import literal, select, union_all
from sqlalchemy.orm import Session

from app.modules.clients.model import ClientNote
from app.modules.processes.model import Process, ProcessMovement
from app.modules.users.model import User


class TimelineRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_recent_activity(self, client_id: int, limit: int) -> list[dict]:
        movements_q = (
            select(
                literal("movement").label("kind"),
                ProcessMovement.process_id.label("process_id"),
                literal(None).label("note_id"),
                ProcessMovement.title.label("title"),
                ProcessMovement.description.label("content"),
                ProcessMovement.occurred_at.label("occurred_at"),
                ProcessMovement.created_by.label("actor_id"),
                User.name.label("actor_name"),
            )
            .join(Process, Process.id == ProcessMovement.process_id)
            .outerjoin(User, User.id == ProcessMovement.created_by)
            .where(Process.client_id == client_id)
        )

        notes_q = (
            select(
                literal("client_note").label("kind"),
                literal(None).label("process_id"),
                ClientNote.id.label("note_id"),
                literal(None).label("title"),
                ClientNote.content.label("content"),
                ClientNote.created_at.label("occurred_at"),
                ClientNote.created_by.label("actor_id"),
                User.name.label("actor_name"),
            )
            .outerjoin(User, User.id == ClientNote.created_by)
            .where(ClientNote.client_id == client_id)
        )

        unioned = union_all(movements_q, notes_q).subquery()
        stmt = select(unioned).order_by(unioned.c.occurred_at.desc()).limit(limit)

        rows = self.db.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
