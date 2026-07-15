from backend.app.main import PERMISSION_CATALOG, User, get_user_permissions, require_permission


def permission_catalog() -> list[str]:
    return list(PERMISSION_CATALOG)


def user_can(user: User, permission: str) -> bool:
    return permission in get_user_permissions(user)


def describe_permissions(user: User) -> dict[str, bool]:
    granted = get_user_permissions(user)
    return {permission: permission in granted for permission in PERMISSION_CATALOG}


__all__ = [
    "PERMISSION_CATALOG",
    "permission_catalog",
    "user_can",
    "describe_permissions",
    "get_user_permissions",
    "require_permission",
]
