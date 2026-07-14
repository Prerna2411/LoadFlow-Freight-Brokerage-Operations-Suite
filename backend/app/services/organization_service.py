from sqlalchemy.orm import Session

from backend.app.repositories.organization_repository import OrganizationRepository


class OrganizationService:
    def __init__(self, db: Session):
        self.repository = OrganizationRepository(db)

    def list_carriers(self):
        return self.repository.list("carrier")
