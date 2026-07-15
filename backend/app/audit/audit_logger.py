import json
from typing import Any

from sqlalchemy.orm import Session

from backend.app.main import AuditEvent, User, log_event


class AuditLogger:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        user: User | None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        log_event(self.db, user, action, entity_type, entity_id, details)

    def permission_denied(self, user: User | None, attempted: str, entity_type: str = "permission", entity_id: int | None = None) -> None:
        self.record(user, "permission_denied", entity_type, entity_id, {"attempted": attempted})

    def serialize(self, event: AuditEvent) -> dict[str, Any]:
        return {
            "id": event.id,
            "user_id": event.user_id,
            "organization_id": event.organization_id,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "action": event.action,
            "details": json.loads(event.details or "{}"),
            "created_at": event.created_at.isoformat(),
        }


__all__ = ["AuditLogger", "log_event"]
