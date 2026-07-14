from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import Permission, Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_org(self, organization_id: int) -> list[Role]:
        return list(self.db.scalars(select(Role).where(Role.organization_id == organization_id)).all())

    def get_for_org(self, role_id: int, organization_id: int) -> Role | None:
        role = self.db.get(Role, role_id)
        return role if role and role.organization_id == organization_id else None

    def create(self, organization_id: int, name: str, permission_codes: list[str]) -> Role:
        permissions = self.db.scalars(select(Permission).where(Permission.code.in_(permission_codes))).all()
        role = Role(organization_id=organization_id, name=name, permissions=list(permissions))
        self.db.add(role)
        self.db.flush()
        return role
