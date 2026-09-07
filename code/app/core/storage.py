"""
Local disk-backed file storage keyed by UUID, never by the original
filename -- so repeated uploads (even of files with the same name) never
collide or silently overwrite each other.

Swappable later for S3/GCS etc. by implementing the same interface.
"""
import uuid
from pathlib import Path


class UploadStorage:
    def __init__(self, upload_dir: Path | str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _extension_for(self, original_filename: str | None) -> str:
        if not original_filename or "." not in original_filename:
            return ""
        return "." + original_filename.rsplit(".", 1)[-1].lower()

    def save(self, file_bytes: bytes, original_filename: str | None) -> str:
        """Writes the bytes under a fresh UUID-based key and returns that key.
        A collision with an existing key is astronomically unlikely, but if
        one ever happened this would raise rather than silently overwrite."""
        ext = self._extension_for(original_filename)
        storage_key = f"{uuid.uuid4()}{ext}"
        path = self.upload_dir / storage_key
        if path.exists():  # pragma: no cover - defense in depth only
            raise FileExistsError(f"Storage key collision: {storage_key}")
        path.write_bytes(file_bytes)
        return storage_key

    def read(self, storage_key: str) -> bytes:
        return self.path_for(storage_key).read_bytes()

    def exists(self, storage_key: str) -> bool:
        return self.path_for(storage_key).exists()

    def path_for(self, storage_key: str) -> Path:
        return self.upload_dir / storage_key
