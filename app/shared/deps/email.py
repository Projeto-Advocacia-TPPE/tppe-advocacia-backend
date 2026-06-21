from functools import lru_cache

from app.config.settings import get_settings
from app.modules.email.fake_service import FakeEmailService
from app.modules.email.resend_service import ResendEmailService


@lru_cache(maxsize=1)
def get_email_service() -> ResendEmailService | FakeEmailService:
    settings = get_settings()
    if settings.app_env == "production":
        return ResendEmailService()
    return FakeEmailService()
