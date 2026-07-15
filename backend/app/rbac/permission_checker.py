from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.main import Load, User, deny, get_user_permissions, load_for_user, require_permission


@dataclass
class PermissionChecker:
    db: Session
    user: User

    def permissions(self) -> set[str]:
        return get_user_permissions(self.user)

    def has(self, permission: str) -> bool:
        return permission in self.permissions()

    def require(self, permission: str) -> None:
        require_permission(self.db, self.user, permission)

    def scoped_load(self, load_id: int) -> Load:
        return load_for_user(self.db, self.user, load_id)

    def require_org(self, organization_id: int | None, action: str) -> None:
        if self.user.organization_id != organization_id:
            deny(self.db, self.user, action, "organization", organization_id)


def can(user: User, permission: str) -> bool:
    return permission in get_user_permissions(user)
