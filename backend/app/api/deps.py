from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.main import User, current_user, get_db, require_permission



DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(current_user)]


def require(permission: str) -> Callable[[DbSession, CurrentUser], User]:
    def dependency(db: DbSession, user: CurrentUser) -> User:
        require_permission(db, user, permission)
        return user

    return dependency


def require_staff_manager(db: DbSession, user: CurrentUser) -> User:
    require_permission(db, user, "staff.manage")
    return user


__all__ = [
    "CurrentUser",
    "DbSession",
    "current_user",
    "get_db",
    "require",
    "require_permission",
    "require_staff_manager",
]
