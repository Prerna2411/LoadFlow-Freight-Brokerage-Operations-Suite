from datetime import date


def insurance_is_active(expiry: date) -> bool:
    return expiry >= date.today()
