def normalize_email(email: str) -> str:
    return email.strip().lower()


def require_non_empty(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()
