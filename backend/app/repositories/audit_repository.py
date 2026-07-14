from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import AuditEvent


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_org(self, organization_id: int, limit: int = 100) -> list[AuditEvent]:
        stmt = select(AuditEvent).where(AuditEvent.organization_id == organization_id).order_by(AuditEvent.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())
