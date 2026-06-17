from unittest.mock import MagicMock

import pytest

from app.modules.media.schema import MediaUploadResponse
from app.modules.media.service import MediaService
from app.shared.exceptions import MediaNotFoundError


@pytest.fixture
def storage():
    return MagicMock()


@pytest.fixture
def service(storage):
    return MediaService(storage)


class TestUpload:
    def test_returns_absolute_url(self, service, storage):
        storage.save.return_value = "abc123.jpg"
        result = service.upload(MagicMock(), "http://localhost:8000/")
        assert result == MediaUploadResponse(
            url="http://localhost:8000/api/v1/media/abc123.jpg"
        )

    def test_url_handles_base_url_without_trailing_slash(self, service, storage):
        storage.save.return_value = "abc123.png"
        result = service.upload(MagicMock(), "http://localhost:8000")
        assert result.url == "http://localhost:8000/api/v1/media/abc123.png"

    def test_delegates_to_storage(self, service, storage):
        storage.save.return_value = "xyz.webp"
        fake_file = MagicMock()
        service.upload(fake_file, "http://localhost:8000/")
        storage.save.assert_called_once_with(fake_file)


class TestGetFilePath:
    VALID_NAME = "12345678-1234-1234-1234-123456789012.jpg"

    def test_returns_path_when_file_exists(self, service, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "app.modules.media.service.get_settings",
            lambda: MagicMock(upload_dir=str(tmp_path)),
        )
        svc = MediaService(MagicMock())
        file = tmp_path / self.VALID_NAME
        file.write_bytes(b"fake")
        assert svc.get_file_path(self.VALID_NAME) == file.resolve()

    def test_raises_when_file_missing(self, service, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "app.modules.media.service.get_settings",
            lambda: MagicMock(upload_dir=str(tmp_path)),
        )
        svc = MediaService(MagicMock())
        with pytest.raises(MediaNotFoundError):
            svc.get_file_path(self.VALID_NAME)

    @pytest.mark.parametrize(
        "name",
        [
            "../etc/passwd",
            "..\\..\\.env",
            "/etc/passwd",
            "test.jpg",
            "abc.jpg",
            "12345678-1234-1234-1234-123456789012",
            "12345678-1234-1234-1234-123456789012.JPG",
            "12345678-1234-1234-1234-123456789012/..",
        ],
    )
    def test_rejects_invalid_or_traversal_names(
        self, service, tmp_path, monkeypatch, name
    ):
        monkeypatch.setattr(
            "app.modules.media.service.get_settings",
            lambda: MagicMock(upload_dir=str(tmp_path)),
        )
        svc = MediaService(MagicMock())
        with pytest.raises(MediaNotFoundError):
            svc.get_file_path(name)
