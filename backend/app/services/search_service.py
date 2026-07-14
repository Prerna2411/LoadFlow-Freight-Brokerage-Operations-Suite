from backend.app.main import Load


def matches_load(load: Load, query: str) -> bool:
    value = query.lower()
    return any(value in field.lower() for field in [load.reference, load.origin, load.destination, load.commodity])
