from sqlalchemy.orm import Session

from backend.app.main import User, log_event


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record(self, user: User | None, action: str, entity_type: str, entity_id: int | None = None, details: dict | None = None) -> None:
        log_event(self.db, user, action, entity_type, entity_id, details)
