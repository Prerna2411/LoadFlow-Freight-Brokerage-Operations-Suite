from sqlalchemy.orm import Session

from backend.app.main import Notification


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, message: str, notification_type: str, organization_id: int | None = None, user_id: int | None = None) -> Notification:
        notification = Notification(organization_id=organization_id, user_id=user_id, type=notification_type, message=message)
        self.db.add(notification)
        self.db.flush()
        return notification
