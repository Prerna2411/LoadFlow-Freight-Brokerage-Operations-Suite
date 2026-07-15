VALID_AUTHORITY_STATUSES = {"active", "pending", "lapsed"}


def normalize_authority_status(status: str) -> str:
    return status.strip().lower()


def authority_is_active(status: str) -> bool:
    return normalize_authority_status(status) == "active"


def authority_reason(status: str) -> str | None:
    normalized = normalize_authority_status(status)
    if normalized not in VALID_AUTHORITY_STATUSES:
        return f"unknown authority status: {status}"
    if normalized != "active":
        return f"authority {normalized}"
    return None
