from functools import wraps

from backend.app.main import require_permission


def permission_required(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            db = kwargs.get("db")
            user = kwargs.get("user")
            if db is not None and user is not None:
                require_permission(db, user, permission)
            return func(*args, **kwargs)

        return wrapper

    return decorator
