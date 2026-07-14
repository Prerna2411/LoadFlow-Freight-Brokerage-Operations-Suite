from pathlib import Path

from backend.app.main import UPLOAD_DIR


class PodService:
    def storage_path(self, load_id: int, filename: str) -> Path:
        return UPLOAD_DIR / f"{load_id}-{filename}"
