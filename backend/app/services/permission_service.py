from backend.app.main import PERMISSION_CATALOG


class PermissionService:
    def catalog(self) -> list[dict[str, str]]:
        return [{"code": code, "description": code.replace(".", " ").title()} for code in PERMISSION_CATALOG]
