from datetime import date, timedelta


class DashboardService:
    def build(self, account_type: str, loads: list[dict], carrier_compliance: list[dict] | None = None) -> dict:
        flagged = [load for load in loads if load.get("compliance_flag")]
        expiring = [
            record for record in (carrier_compliance or [])
            if date.fromisoformat(record["insurance_expiry"]) <= date.today() + timedelta(days=30)
        ]
        return {
            "account_type": account_type,
            "counts": {"loads": len(loads), "flagged": len(flagged)},
            "alerts": {"compliance_flags": flagged, "insurance_expiring": expiring},
        }
