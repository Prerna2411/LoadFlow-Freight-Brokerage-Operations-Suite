from sqlalchemy.orm import Session

from backend.app.main import Load, User, apply_compliance, load_for_user, record_status_history, transition


class LoadService:
    def __init__(self, db: Session):
        self.db = db

    def get_scoped(self, user: User, load_id: int) -> Load:
        return load_for_user(self.db, user, load_id)

    def assign_carrier(self, load: Load, carrier_org_id: int, user: User) -> None:
        previous = load.status
        load.carrier_org_id = carrier_org_id
        load.status = "Carrier Assigned"
        apply_compliance(self.db, load, carrier_org_id)
        record_status_history(self.db, load, previous, load.status, user, "Carrier assigned")

    def advance(self, load: Load, status: str, user: User) -> None:
        transition(load, status, self.db, user, "Status updated")
