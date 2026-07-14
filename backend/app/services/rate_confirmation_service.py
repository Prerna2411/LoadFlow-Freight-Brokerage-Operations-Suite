import json

from sqlalchemy.orm import Session

from backend.app.main import RateConfirmation, User, transition
from backend.app.repositories.rate_repository import RateRepository


class RateConfirmationService:
    def __init__(self, db: Session):
        self.db = db
        self.rates = RateRepository(db)

    def create_version(self, *, load, user: User, base_rate: float, accessorials: list[dict]) -> RateConfirmation:
        rate = RateConfirmation(
            load_id=load.id,
            carrier_org_id=load.carrier_org_id,
            version=self.rates.next_version(load.id),
            base_rate=base_rate,
            accessorials=json.dumps(accessorials),
            confirmed_by_user_id=user.id,
        )
        self.db.add(rate)
        self.db.flush()
        load.current_rate_confirmation_id = rate.id
        transition(load, "Rate Confirmed", self.db, user, "Rate confirmation accepted")
        return rate
