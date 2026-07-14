from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import Pod


class PodRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_load(self, load_id: int) -> Pod | None:
        return self.db.scalar(select(Pod).where(Pod.load_id == load_id))
