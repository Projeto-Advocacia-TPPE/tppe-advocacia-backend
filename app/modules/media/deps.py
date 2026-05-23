from app.modules.media.service import MediaService
from app.modules.media.storage.local import LocalStorageProvider


def get_media_service() -> MediaService:
    return MediaService(LocalStorageProvider())
