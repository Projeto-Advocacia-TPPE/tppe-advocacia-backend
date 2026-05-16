from fastapi import UploadFile

from app.modules.media.schema import MediaUploadResponse
from app.modules.media.service import MediaService
from app.modules.media.storage.local import LocalStorageProvider
from app.modules.media.storage.protocol import StorageProvider


class MediaController:
    def __init__(self, storage: StorageProvider | None = None) -> None:
        self.service = MediaService(storage or LocalStorageProvider())

    def upload(self, file: UploadFile, base_url: str) -> MediaUploadResponse:
        return self.service.upload(file, base_url)

    def get_file_path(self, filename: str):
        return self.service.get_file_path(filename)
