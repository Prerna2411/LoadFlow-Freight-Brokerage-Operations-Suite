from pydantic import BaseModel


class OrganizationOut(BaseModel):
    id: int
    name: str
    type: str
