from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: int | None = None
    created_at: str
