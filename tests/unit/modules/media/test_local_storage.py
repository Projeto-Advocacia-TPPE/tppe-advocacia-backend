import io
from unittest.mock import MagicMock, patch

import pytest

from app.modules.media.storage.local import LocalStorageProvider
from app.shared.exceptions import FileTooLargeError, InvalidMimeTypeError

FAKE_JPEG_MAGIC = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"\x00" * 100
FAKE_PDF_MAGIC = b"%PDF-1.4" + b"\x00" * 100


def make_upload_file(content: bytes, filename: str = "test.jpg"):
    mock = MagicMock()
    mock.filename = filename
    mock.file = io.BytesIO(content)
    return mock


@pytest.fixture
def provider(tmp_path):
    settings_mock = MagicMock(
        upload_dir=str(tmp_path),
        max_file_size_mb=1,
        allowed_mime_types=["image/jpeg", "image/png", "image/webp", "image/gif"],
    )
    with patch(
        "app.modules.media.storage.local.get_settings", return_value=settings_mock
    ):
        yield LocalStorageProvider()


class TestSave:
    def test_saves_valid_jpeg_and_returns_filename(self, provider, tmp_path):
        file = make_upload_file(FAKE_JPEG_MAGIC, "photo.jpg")
        with patch("filetype.guess") as mock_guess:
            mock_guess.return_value = MagicMock(mime="image/jpeg", extension="jpg")
            filename = provider.save(file)

        assert filename.endswith(".jpg")
        assert (tmp_path / filename).exists()

    def test_filename_is_unique_uuid(self, provider, tmp_path):
        file1 = make_upload_file(FAKE_JPEG_MAGIC, "photo.jpg")
        file2 = make_upload_file(FAKE_JPEG_MAGIC, "photo.jpg")
        with patch("filetype.guess") as mock_guess:
            mock_guess.return_value = MagicMock(mime="image/jpeg", extension="jpg")
            name1 = provider.save(file1)
            name2 = provider.save(file2)

        assert name1 != name2

    def test_raises_when_file_too_large(self, provider):
        big_content = b"\x00" * (2 * 1024 * 1024)
        file = make_upload_file(big_content, "big.jpg")
        with pytest.raises(FileTooLargeError):
            provider.save(file)

    def test_raises_on_invalid_mime_type(self, provider):
        file = make_upload_file(FAKE_PDF_MAGIC, "doc.pdf")
        with patch("filetype.guess") as mock_guess:
            mock_guess.return_value = MagicMock(mime="application/pdf", extension="pdf")
            with pytest.raises(InvalidMimeTypeError):
                provider.save(file)

    def test_raises_when_mime_undetectable(self, provider):
        file = make_upload_file(b"random garbage", "file.xyz")
        with patch("filetype.guess", return_value=None):
            with pytest.raises(InvalidMimeTypeError):
                provider.save(file)
