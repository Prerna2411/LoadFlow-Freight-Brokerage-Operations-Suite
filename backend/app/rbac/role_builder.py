from backend.app.main import PERMISSION_CATALOG


def build_role_payload(name: str, permissions: list[str]) -> dict:
    invalid = set(permissions) - set(PERMISSION_CATALOG)
    if invalid:
        raise ValueError(f"Unknown permissions: {sorted(invalid)}")
    return {"name": name, "permissions": permissions}
