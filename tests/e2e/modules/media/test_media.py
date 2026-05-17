import io
from unittest.mock import MagicMock, patch

import pytest

FAKE_JPEG = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"\x00" * 200


@pytest.fixture
def jpeg_file():
    return ("file", ("photo.jpg", io.BytesIO(FAKE_JPEG), "image/jpeg"))


class TestUpload:
    def test_upload_without_token_returns_401(self, client, jpeg_file):
        response = client.post("/api/v1/media/upload", files=[jpeg_file])
        assert response.status_code == 401

    def test_upload_with_invalid_mime_returns_415(self, client, user_headers, tmp_path):
        fake_settings = MagicMock(
            upload_dir=str(tmp_path),
            max_file_size_mb=5,
            allowed_mime_types=["image/jpeg", "image/png", "image/webp", "image/gif"],
        )
        pdf_content = b"%PDF-1.4" + b"\x00" * 100
        with patch(
            "app.modules.media.storage.local.get_settings", return_value=fake_settings
        ):
            with patch("filetype.guess") as mock_guess:
                mock_guess.return_value = MagicMock(
                    mime="application/pdf", extension="pdf"
                )
                response = client.post(
                    "/api/v1/media/upload",
                    files=[
                        (
                            "file",
                            ("doc.pdf", io.BytesIO(pdf_content), "application/pdf"),
                        )
                    ],
                    headers=user_headers,
                )
        assert response.status_code == 415
        assert response.json()["error"]["code"] == "INVALID_MIME_TYPE"

    def test_upload_exceeding_size_returns_413(self, client, user_headers, tmp_path):
        fake_settings = MagicMock(
            upload_dir=str(tmp_path),
            max_file_size_mb=1,
            allowed_mime_types=["image/jpeg", "image/png", "image/webp", "image/gif"],
        )
        big = b"\x00" * (2 * 1024 * 1024)
        with patch(
            "app.modules.media.storage.local.get_settings", return_value=fake_settings
        ):
            response = client.post(
                "/api/v1/media/upload",
                files=[("file", ("big.jpg", io.BytesIO(big), "image/jpeg"))],
                headers=user_headers,
            )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "FILE_TOO_LARGE"

    def test_upload_valid_jpeg_returns_201_with_url(
        self, client, user_headers, tmp_path
    ):
        fake_settings = MagicMock(
            upload_dir=str(tmp_path),
            max_file_size_mb=5,
            allowed_mime_types=["image/jpeg", "image/png", "image/webp", "image/gif"],
        )
        with patch(
            "app.modules.media.storage.local.get_settings", return_value=fake_settings
        ):
            with patch("filetype.guess") as mock_guess:
                mock_guess.return_value = MagicMock(mime="image/jpeg", extension="jpg")
                response = client.post(
                    "/api/v1/media/upload",
                    files=[
                        ("file", ("photo.jpg", io.BytesIO(FAKE_JPEG), "image/jpeg"))
                    ],
                    headers=user_headers,
                )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        url = body["data"]["url"]
        assert "/api/v1/media/" in url
        assert url.endswith(".jpg")


class TestServeFile:
    VALID_NAME = "12345678-1234-1234-1234-123456789012.jpg"

    def test_serve_existing_file_returns_200(self, client, tmp_path):
        fake_settings = MagicMock(upload_dir=str(tmp_path))
        (tmp_path / self.VALID_NAME).write_bytes(FAKE_JPEG)
        with patch(
            "app.modules.media.service.get_settings", return_value=fake_settings
        ):
            response = client.get(f"/api/v1/media/{self.VALID_NAME}")
        assert response.status_code == 200

    def test_serve_missing_file_returns_404(self, client, tmp_path):
        fake_settings = MagicMock(upload_dir=str(tmp_path))
        with patch(
            "app.modules.media.service.get_settings", return_value=fake_settings
        ):
            response = client.get(f"/api/v1/media/{self.VALID_NAME}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"

    def test_serve_rejects_invalid_filename_returns_404(self, client, tmp_path):
        fake_settings = MagicMock(upload_dir=str(tmp_path))
        with patch(
            "app.modules.media.service.get_settings", return_value=fake_settings
        ):
            response = client.get("/api/v1/media/test.jpg")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"

    def test_serve_rejects_path_traversal_returns_404(self, client, tmp_path):
        fake_settings = MagicMock(upload_dir=str(tmp_path))
        secret = tmp_path.parent / "secret.env"
        secret.write_bytes(b"JWT_SECRET_KEY=leaked")
        with patch(
            "app.modules.media.service.get_settings", return_value=fake_settings
        ):
            response = client.get("/api/v1/media/..%2Fsecret.env")
        assert response.status_code == 404
        assert b"JWT_SECRET_KEY=leaked" not in response.content
