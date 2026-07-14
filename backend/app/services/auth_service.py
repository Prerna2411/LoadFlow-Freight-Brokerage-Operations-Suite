from sqlalchemy.orm import Session

from backend.app.main import create_token, user_payload, verify_password
from backend.app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def authenticate(self, email: str, password: str) -> tuple[str, dict] | None:
        user = self.users.by_email(email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return create_token(user), user_payload(user)
