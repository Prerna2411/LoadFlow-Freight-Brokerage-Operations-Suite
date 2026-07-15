from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import Load, LoadStatusHistory, User, record_status_history


class ActivityTracker:
    def __init__(self, db: Session):
        self.db = db

    def status_change(self, load: Load, from_status: str | None, to_status: str, user: User | None, note: str | None = None) -> None:
        record_status_history(self.db, load, from_status, to_status, user, note)

    def timeline(self, load_id: int) -> list[LoadStatusHistory]:
        stmt = select(LoadStatusHistory).where(LoadStatusHistory.load_id == load_id).order_by(LoadStatusHistory.created_at)
        return list(self.db.scalars(stmt).all())

    def serialize(self, row: LoadStatusHistory) -> dict:
        return {
            "id": row.id,
            "load_id": row.load_id,
            "from_status": row.from_status,
            "to_status": row.to_status,
            "changed_by_user_id": row.changed_by_user_id,
            "note": row.note,
            "created_at": row.created_at.isoformat(),
        }


__all__ = ["ActivityTracker", "record_status_history"]
