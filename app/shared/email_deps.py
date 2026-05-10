from app.modules.email.resend_service import ResendEmailService


def get_email_service() -> ResendEmailService:
    return ResendEmailService()
