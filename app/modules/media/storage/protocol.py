from typing import Protocol

from fastapi import UploadFile


class StorageProvider(Protocol):
    def save(self, file: UploadFile) -> str: ...
