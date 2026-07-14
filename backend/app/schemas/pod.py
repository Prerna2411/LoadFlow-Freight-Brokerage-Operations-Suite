from pydantic import BaseModel


class PodOut(BaseModel):
    id: int
    load_id: int
    file_name: str
    url: str
    verified_at: str | None = None
