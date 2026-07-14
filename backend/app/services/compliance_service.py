import json
from datetime import date

from backend.app.main import ComplianceRecord, Load


class ComplianceService:
    def reasons(self, record: ComplianceRecord | None, load: Load) -> list[str]:
        if not record:
            return ["missing compliance record"]
        reasons: list[str] = []
        if record.insurance_expiry < date.today():
            reasons.append("insurance expired")
        if record.authority_status != "active":
            reasons.append(f"authority {record.authority_status}")
        if load.equipment_type not in json.loads(record.approved_equipment):
            reasons.append("equipment not approved")
        if load.commodity not in json.loads(record.approved_commodities):
            reasons.append("commodity not approved")
        return reasons
