from datetime import date, timedelta


def insurance_is_active(expiry: date, today: date | None = None) -> bool:
    today = today or date.today()
    return expiry >= today


def insurance_expires_within(expiry: date, days: int = 30, today: date | None = None) -> bool:
    today = today or date.today()
    return today <= expiry <= today + timedelta(days=days)


def insurance_reason(expiry: date, today: date | None = None) -> str | None:
    today = today or date.today()
    if expiry < today:
        return "insurance expired"
    if insurance_expires_within(expiry, today=today):
        return "insurance renewal due soon"
    return None
