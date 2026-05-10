class FakeEmailService:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, html: str) -> None:
        self.sent.append({"to": to, "subject": subject, "html": html})
