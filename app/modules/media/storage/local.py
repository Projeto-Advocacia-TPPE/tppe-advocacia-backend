import uuid
from pathlib import Path

import filetype
from fastapi import UploadFile

from app.config.settings import get_settings
from app.shared.exceptions import FileTooLargeError, InvalidMimeTypeError

_CHUNK_SIZE = 64 * 1024


class LocalStorageProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file: UploadFile) -> str:
        max_bytes = self.settings.max_file_size_mb * 1024 * 1024

        declared_size = getattr(file, "size", None)
        if declared_size is not None and declared_size > max_bytes:
            raise FileTooLargeError(self.settings.max_file_size_mb)

        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = file.file.read(_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise FileTooLargeError(self.settings.max_file_size_mb)
            chunks.append(chunk)
        content = b"".join(chunks)

        kind = filetype.guess(content)
        mime = kind.mime if kind else None
        if mime not in self.settings.allowed_mime_types:
            raise InvalidMimeTypeError(self.settings.allowed_mime_types)

        filename = f"{uuid.uuid4()}.{kind.extension}"
        (self.upload_dir / filename).write_bytes(content)

        return filename
