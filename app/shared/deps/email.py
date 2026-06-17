from functools import lru_cache

from app.modules.email.resend_service import ResendEmailService


@lru_cache(maxsize=1)
def get_email_service() -> ResendEmailService:
    return ResendEmailService()
