from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.main import RateConfirmation


class RateRepository:
    def __init__(self, db: Session):
        self.db = db

    def next_version(self, load_id: int) -> int:
        latest = self.db.scalar(select(func.max(RateConfirmation.version)).where(RateConfirmation.load_id == load_id)) or 0
        return latest + 1

    def list_for_load(self, load_id: int) -> list[RateConfirmation]:
        return list(self.db.scalars(select(RateConfirmation).where(RateConfirmation.load_id == load_id).order_by(RateConfirmation.version)).all())
