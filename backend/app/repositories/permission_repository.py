from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import PERMISSION_CATALOG, Permission


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def seed_catalog(self) -> None:
        for code in PERMISSION_CATALOG:
            if not self.db.scalar(select(Permission).where(Permission.code == code)):
                self.db.add(Permission(code=code, description=code.replace(".", " ").title()))

    def list(self) -> list[Permission]:
        return list(self.db.scalars(select(Permission).order_by(Permission.code)).all())
