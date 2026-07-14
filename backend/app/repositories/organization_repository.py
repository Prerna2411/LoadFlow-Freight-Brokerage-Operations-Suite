from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import Organization


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, organization_type: str | None = None) -> list[Organization]:
        stmt = select(Organization)
        if organization_type:
            stmt = stmt.where(Organization.type == organization_type)
        return list(self.db.scalars(stmt).all())

    def get(self, organization_id: int) -> Organization | None:
        return self.db.get(Organization, organization_id)

    def create(self, name: str, organization_type: str) -> Organization:
        org = Organization(name=name, type=organization_type)
        self.db.add(org)
        self.db.flush()
        return org
