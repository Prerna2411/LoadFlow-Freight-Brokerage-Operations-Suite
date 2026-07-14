from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import Load


class LoadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, load_id: int) -> Load | None:
        return self.db.get(Load, load_id)

    def scoped(self, *, account_type: str, user_id: int, organization_id: int | None, q: str | None = None, status: str | None = None) -> list[Load]:
        stmt = select(Load)
        if account_type == "broker":
            stmt = stmt.where(Load.broker_org_id == organization_id)
        elif account_type == "carrier":
            stmt = stmt.where(Load.carrier_org_id == organization_id)
        else:
            stmt = stmt.where(Load.shipper_user_id == user_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where((Load.reference.like(like)) | (Load.origin.like(like)) | (Load.destination.like(like)) | (Load.commodity.like(like)))
        if status:
            stmt = stmt.where(Load.status == status)
        return list(self.db.scalars(stmt.order_by(Load.created_at.desc())).all())

    def create(self, **values) -> Load:
        load = Load(**values)
        self.db.add(load)
        self.db.flush()
        return load
