from backend.app.main import PERMISSION_CATALOG
from backend.app.repositories.role_repository import RoleRepository


class RoleService:
    def __init__(self, repository: RoleRepository):
        self.repository = repository

    def validate_permissions(self, codes: list[str]) -> None:
        unknown = set(codes) - set(PERMISSION_CATALOG)
        if unknown:
            raise ValueError(f"Unknown permissions: {sorted(unknown)}")
