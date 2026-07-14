from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.main import Role, User, hash_password


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def list_shippers(self) -> list[User]:
        return list(self.db.scalars(select(User).where(User.account_type == "shipper")).all())

    def create_staff(self, *, name: str, email: str, password: str, account_type: str, organization_id: int, role: Role) -> User:
        user = User(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            account_type=account_type,
            organization_id=organization_id,
            role_id=role.id,
            roles=[role],
        )
        self.db.add(user)
        self.db.flush()
        return user
