from pathlib import Path

from fastapi import UploadFile

from app.config.settings import get_settings
from app.modules.media.schema import MediaUploadResponse
from app.modules.media.storage.protocol import StorageProvider
from app.shared.exceptions import MediaNotFoundError


class MediaService:
    def __init__(self, storage: StorageProvider) -> None:
        self.storage = storage
        self.settings = get_settings()

    def upload(self, file: UploadFile, base_url: str) -> MediaUploadResponse:
        filename = self.storage.save(file)
        url = f"{base_url.rstrip('/')}/api/v1/media/{filename}"
        return MediaUploadResponse(url=url)

    def get_file_path(self, filename: str) -> Path:
        path = Path(self.settings.upload_dir) / filename
        if not path.exists():
            raise MediaNotFoundError()
        return path
