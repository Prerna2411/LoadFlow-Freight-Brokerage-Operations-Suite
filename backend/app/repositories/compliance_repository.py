from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import ComplianceRecord


class ComplianceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_carrier(self, carrier_org_id: int) -> ComplianceRecord | None:
        return self.db.scalar(select(ComplianceRecord).where(ComplianceRecord.carrier_org_id == carrier_org_id))

    def list(self) -> list[ComplianceRecord]:
        return list(self.db.scalars(select(ComplianceRecord)).all())

    def upsert(self, carrier_org_id: int, **values) -> ComplianceRecord:
        record = self.get_for_carrier(carrier_org_id)
        if record:
            for key, value in values.items():
                setattr(record, key, value)
        else:
            record = ComplianceRecord(carrier_org_id=carrier_org_id, **values)
            self.db.add(record)
        self.db.flush()
        return record
