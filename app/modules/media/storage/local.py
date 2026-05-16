import uuid
from pathlib import Path

import filetype
from fastapi import UploadFile

from app.config.settings import get_settings
from app.shared.exceptions import FileTooLargeError, InvalidMimeTypeError


class LocalStorageProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file: UploadFile) -> str:
        content = file.file.read()

        max_bytes = self.settings.max_file_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise FileTooLargeError(self.settings.max_file_size_mb)

        kind = filetype.guess(content)
        mime = kind.mime if kind else None
        if mime not in self.settings.allowed_mime_types:
            raise InvalidMimeTypeError(self.settings.allowed_mime_types)

        suffix = Path(file.filename or "").suffix or f".{kind.extension}"
        filename = f"{uuid.uuid4()}{suffix}"
        (self.upload_dir / filename).write_bytes(content)

        return filename
