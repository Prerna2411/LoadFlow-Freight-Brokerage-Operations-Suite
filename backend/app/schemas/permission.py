from pydantic import BaseModel


class PermissionOut(BaseModel):
    code: str
    description: str
