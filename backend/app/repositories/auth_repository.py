from backend.app.repositories.user_repository import UserRepository


class AuthRepository(UserRepository):
    """Auth storage is user storage plus password verification in the service layer."""
