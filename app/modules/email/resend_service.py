import resend

from app.config.settings import get_settings


class ResendEmailService:
    def __init__(self) -> None:
        settings = get_settings()
        resend.api_key = settings.resend_api_key
        self._from = settings.resend_from_email

    def send(self, to: str, subject: str, html: str) -> None:
        resend.Emails.send(
            {
                "from": self._from,
                "to": to,
                "subject": subject,
                "html": html,
            }
        )
