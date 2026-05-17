import re
from pathlib import Path

from fastapi import UploadFile

from app.config.settings import get_settings
from app.modules.media.schema import MediaUploadResponse
from app.modules.media.storage.protocol import StorageProvider
from app.shared.exceptions import MediaNotFoundError

_FILENAME_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[a-z0-9]+$"
)


class MediaService:
    def __init__(self, storage: StorageProvider) -> None:
        self.storage = storage
        self.settings = get_settings()

    def upload(self, file: UploadFile, base_url: str) -> MediaUploadResponse:
        filename = self.storage.save(file)
        # TODO: Implement proper URL construction
        url = f"{base_url.rstrip('/')}/api/v1/media/{filename}"
        return MediaUploadResponse(url=url)

    def get_file_path(self, filename: str) -> Path:
        if not _FILENAME_PATTERN.match(filename):
            raise MediaNotFoundError()

        base = Path(self.settings.upload_dir).resolve()
        candidate = (base / filename).resolve()
        if not candidate.is_relative_to(base) or not candidate.is_file():
            raise MediaNotFoundError()
        return candidate
